const API = 'http://127.0.0.1:8000/api/v1';
let token = localStorage.getItem('campus_token');
let conversationId = null;

const $ = (id) => document.getElementById(id);
const request = async (path, options = {}) => {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(API + path, { ...options, headers });
  const body = response.status === 204 ? null : await response.json();
  if (!response.ok) throw new Error(body?.detail || body?.message || '请求失败');
  return body;
};

function showApp(user) {
  $('authView').classList.add('hidden'); $('appView').classList.remove('hidden');
  $('userBox').innerHTML = `<span>${user.nickname}</span><button class="link-button" id="logoutBtn">退出</button>`;
  $('logoutBtn').onclick = () => { localStorage.removeItem('campus_token'); location.reload(); };
  loadData();
}

async function loadData() {
  try {
    const [courses, tasks, overview, conversations] = await Promise.all([request('/courses'), request('/tasks'), request('/stats/overview'), request('/conversations')]);
    if (!courses.length) await request('/courses', { method: 'POST', body: JSON.stringify({ name: '系统设计与实践', semester: '2026 秋' }) });
    const freshCourses = courses.length ? courses : await request('/courses');
    $('courseSelect').innerHTML = freshCourses.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    renderTasks(tasks); renderStats(overview);
    if (conversations.length) conversationId = conversations[0].id; else conversationId = (await request('/conversations', { method: 'POST' })).id;
    renderChat(await request(`/conversations/${conversationId}/messages`));
  } catch (error) { alert(error.message); }
}

function renderStats(data) { $('totalStat').textContent = data.total; $('doneStat').textContent = data.completed; $('rateStat').textContent = `${Math.round(data.completion_rate * 100)}%`; }
function renderTasks(tasks) {
  $('taskList').innerHTML = tasks.length ? tasks.map(task => `<article class="task ${task.status === 'done' ? 'completed' : ''}"><div><strong>${escapeHtml(task.title)}</strong><small>${task.due_at ? `截止 ${task.due_at}` : '无截止日期'} · ${task.priority} · ${task.course_name || ''}</small></div><div class="task-actions"><button data-id="${task.id}" data-status="${task.status === 'done' ? 'todo' : 'done'}">${task.status === 'done' ? '恢复' : '完成'}</button><button class="danger" data-delete="${task.id}">删除</button></div></article>`).join('') : '<p class="empty">还没有任务，添加第一个学习任务吧。</p>';
  document.querySelectorAll('[data-id]').forEach(button => button.onclick = async () => { await request(`/tasks/${button.dataset.id}`, { method: 'PATCH', body: JSON.stringify({ status: button.dataset.status }) }); loadData(); });
  document.querySelectorAll('[data-delete]').forEach(button => button.onclick = async () => { if (confirm('确认删除这个任务吗？')) { await request(`/tasks/${button.dataset.delete}`, { method: 'DELETE' }); loadData(); } });
}
function renderChat(messages) { $('chatLog').innerHTML = messages.map(m => `<div class="bubble ${m.role}">${escapeHtml(m.content)}</div>`).join(''); $('chatLog').scrollTop = $('chatLog').scrollHeight; }
function escapeHtml(value) { return value.replace(/[&<>'"]/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' }[c])); }

$('authForm').onsubmit = async (event) => { event.preventDefault(); try { const body = { account: $('account').value, password: $('password').value }; const result = await request('/auth/login', { method: 'POST', body: JSON.stringify(body) }); token = result.token; localStorage.setItem('campus_token', token); showApp(result.user); } catch (error) { $('authError').textContent = error.message; } };
$('registerBtn').onclick = async () => { try { if (!$('nickname').value) throw new Error('注册时请填写昵称'); const result = await request('/auth/register', { method: 'POST', body: JSON.stringify({ account: $('account').value, password: $('password').value, nickname: $('nickname').value }) }); token = result.token; localStorage.setItem('campus_token', token); showApp(result.user); } catch (error) { $('authError').textContent = error.message; } };
$('taskForm').onsubmit = async (event) => { event.preventDefault(); await request('/tasks', { method: 'POST', body: JSON.stringify({ title: $('taskTitle').value, course_id: Number($('courseSelect').value), due_at: $('dueAt').value || null, priority: $('priority').value }) }); event.target.reset(); loadData(); };
$('refreshBtn').onclick = loadData;
$('chatForm').onsubmit = async (event) => { event.preventDefault(); const input = $('chatInput'); const content = input.value; input.value = ''; $('chatLog').insertAdjacentHTML('beforeend', `<div class="bubble user">${escapeHtml(content)}</div>`); const reply = await request(`/conversations/${conversationId}/messages`, { method: 'POST', body: JSON.stringify({ content }) }); $('chatLog').insertAdjacentHTML('beforeend', `<div class="bubble assistant">${escapeHtml(reply.content)}</div>`); $('chatLog').scrollTop = $('chatLog').scrollHeight; };

if (token) request('/auth/me').then(showApp).catch(() => { localStorage.removeItem('campus_token'); });
