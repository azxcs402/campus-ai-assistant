const API = 'http://127.0.0.1:8000/api/v1';
let token = localStorage.getItem('campus_token');
let conversationId = null;

const $ = (id) => document.getElementById(id);
const request = async (path, options = {}) => {
  const headers = { ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  let response;
  try { response = await fetch(API + path, { ...options, headers }); }
  catch { throw new Error('无法连接服务器，请确认后端服务已启动'); }
  let body = null;
  if (response.status !== 204) {
    try { body = await response.json(); } catch { body = null; }
  }
  if (!response.ok) throw new Error(body?.detail || body?.message || '请求失败');
  return body;
};

async function withBusy(button, action) {
  if (!button || button.disabled) return;
  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = '处理中...';
  try { return await action(); }
  finally { button.disabled = false; button.textContent = originalText; }
}

function showApp(user) {
  $('authView').classList.add('hidden'); $('appView').classList.remove('hidden');
  $('userBox').innerHTML = `<span>${user.nickname}</span><button class="link-button" id="logoutBtn">退出</button>`;
  $('logoutBtn').onclick = () => { localStorage.removeItem('campus_token'); location.reload(); };
  loadData();
}

async function loadData(selectedCourseId = null) {
  try {
    const [courses, tasks, upcoming, overview, conversations] = await Promise.all([request('/courses'), request('/tasks'), request('/tasks/upcoming'), request('/stats/overview'), request('/conversations')]);
    if (!courses.length) await request('/courses', { method: 'POST', body: JSON.stringify({ name: '系统设计与实践', semester: '2026 秋' }) });
    const freshCourses = courses.length ? courses : await request('/courses');
    $('courseSelect').innerHTML = freshCourses.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    $('materialCourseSelect').innerHTML = freshCourses.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    if (selectedCourseId) {
      $('courseSelect').value = String(selectedCourseId);
      $('materialCourseSelect').value = String(selectedCourseId);
    }
    renderTasks(tasks); renderUpcoming(upcoming); renderStats(overview);
    renderMaterials(await request(`/courses/${freshCourses[0].id}/materials`));
    if (conversations.length) conversationId = conversations[0].id; else conversationId = (await request('/conversations', { method: 'POST' })).id;
    renderChat(await request(`/conversations/${conversationId}/messages`));
  } catch (error) { alert(error.message); }
}

function renderStats(data) { $('totalStat').textContent = data.total; $('doneStat').textContent = data.completed; $('rateStat').textContent = `${Math.round(data.completion_rate * 100)}%`; }
function renderTasks(tasks) {
  $('taskList').innerHTML = tasks.length ? tasks.map(task => `<article class="task ${task.status === 'done' ? 'completed' : ''}"><div><strong>${escapeHtml(task.title)}</strong><small>${task.due_at ? `截止 ${task.due_at}` : '无截止日期'} · ${task.priority} · ${task.course_name || ''}</small></div><div class="task-actions"><button data-id="${task.id}" data-status="${task.status === 'done' ? 'todo' : 'done'}">${task.status === 'done' ? '恢复' : '完成'}</button><button class="danger" data-delete="${task.id}">删除</button></div></article>`).join('') : '<p class="empty">还没有任务，添加第一个学习任务吧。</p>';
  document.querySelectorAll('[data-id]').forEach(button => button.onclick = async () => {
    try { await withBusy(button, () => request(`/tasks/${button.dataset.id}`, { method: 'PATCH', body: JSON.stringify({ status: button.dataset.status }) })); await loadData(); }
    catch (error) { alert(error.message); }
  });
  document.querySelectorAll('[data-delete]').forEach(button => button.onclick = async () => {
    if (!confirm('确认删除这个任务吗？')) return;
    try { await withBusy(button, () => request(`/tasks/${button.dataset.delete}`, { method: 'DELETE' })); await loadData(); }
    catch (error) { alert(error.message); }
  });
}
function renderUpcoming(tasks) {
  $('upcomingList').innerHTML = tasks.length ? `<div class="upcoming-title">即将截止</div>${tasks.slice(0, 3).map(task => `<div class="upcoming-item ${task.urgent ? 'urgent' : ''}"><span>${escapeHtml(task.title)}</span><small>${task.remaining_hours <= 0 ? '已逾期' : `${task.remaining_hours} 小时内`}</small></div>`).join('')}` : '';
}
function renderMaterials(materials) {
  $('materialList').innerHTML = materials.length ? materials.map(material => `<article class="task"><div><strong>${escapeHtml(material.title || material.filename)}</strong><small>${escapeHtml(material.filename)} · ${formatBytes(material.file_size)} · ${material.parse_status === 'queued' ? '已保存（解析待接入）' : escapeHtml(material.parse_status)}</small></div><div class="task-actions"><button class="danger" data-material-delete="${material.id}">删除</button></div></article>`).join('') : '<p class="empty">该课程还没有资料。</p>';
  document.querySelectorAll('[data-material-delete]').forEach(button => button.onclick = async () => {
    if (!confirm('确认删除这份资料吗？')) return;
    try { await withBusy(button, () => request(`/materials/${button.dataset.materialDelete}`, { method: 'DELETE' })); await loadData(); }
    catch (error) { alert(error.message); }
  });
}
function formatBytes(bytes) { if (bytes < 1024) return `${bytes} B`; if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`; return `${(bytes / 1024 / 1024).toFixed(1)} MB`; }
function renderChat(messages) { $('chatLog').innerHTML = messages.map(m => `<div class="bubble ${m.role}">${escapeHtml(m.content)}</div>`).join(''); $('chatLog').scrollTop = $('chatLog').scrollHeight; }
function escapeHtml(value) { return value.replace(/[&<>'"]/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' }[c])); }

$('authForm').onsubmit = async (event) => { event.preventDefault(); try { const body = { account: $('account').value, password: $('password').value }; const result = await request('/auth/login', { method: 'POST', body: JSON.stringify(body) }); token = result.token; localStorage.setItem('campus_token', token); showApp(result.user); } catch (error) { $('authError').textContent = error.message; } };
$('registerBtn').onclick = async () => { try { if (!$('nickname').value) throw new Error('注册时请填写昵称'); const result = await request('/auth/register', { method: 'POST', body: JSON.stringify({ account: $('account').value, password: $('password').value, nickname: $('nickname').value }) }); token = result.token; localStorage.setItem('campus_token', token); showApp(result.user); } catch (error) { $('authError').textContent = error.message; } };
 $('taskForm').onsubmit = async (event) => {
  event.preventDefault();
  const button = event.submitter;
  try {
    await withBusy(button, () => request('/tasks', { method: 'POST', body: JSON.stringify({ title: $('taskTitle').value.trim(), course_id: Number($('courseSelect').value), due_at: $('dueAt').value || null, priority: $('priority').value }) }));
    event.target.reset(); await loadData();
  } catch (error) { alert(error.message); }
 };
$('refreshBtn').onclick = loadData;
$('createCourseBtn').onclick = async () => {
  const name = prompt('请输入课程名称');
  if (name === null) return;
  const trimmedName = name.trim();
  if (!trimmedName) { alert('课程名称不能为空'); return; }
  const semester = prompt('请输入学期（可选，例如：2026 秋）');
  try {
    const course = await withBusy($('createCourseBtn'), () => request('/courses', {
      method: 'POST',
      body: JSON.stringify({ name: trimmedName, semester: semester?.trim() || null }),
    }));
    await loadData(course.id);
    alert(`课程“${course.name}”创建成功`);
  } catch (error) { alert(error.message); }
};
$('materialCourseSelect').onchange = async () => {
  try { await loadMaterials($('materialCourseSelect').value); }
  catch (error) { alert(error.message); }
};
async function loadMaterials(courseId) { renderMaterials(await request(`/courses/${courseId}/materials`)); }
 $('materialForm').onsubmit = async (event) => {
  event.preventDefault();
  const button = event.submitter; const file = $('materialFile').files[0];
  if (!file) return;
  const data = new FormData(); data.append('course_id', $('materialCourseSelect').value); data.append('file', file);
  if ($('materialTitle').value.trim()) data.append('title', $('materialTitle').value.trim());
  try { await withBusy(button, () => request('/materials', { method: 'POST', body: data })); event.target.reset(); await loadData(); }
  catch (error) { alert(error.message); }
 };
 $('chatForm').onsubmit = async (event) => {
  event.preventDefault();
  const input = $('chatInput'); const content = input.value.trim(); const button = event.submitter;
  if (!content || !conversationId) return;
  input.value = ''; $('chatLog').insertAdjacentHTML('beforeend', `<div class="bubble user">${escapeHtml(content)}</div>`);
  try {
    const reply = await withBusy(button, () => request(`/conversations/${conversationId}/messages`, { method: 'POST', body: JSON.stringify({ content }) }));
    $('chatLog').insertAdjacentHTML('beforeend', `<div class="bubble assistant">${escapeHtml(reply.content)}</div>`);
  } catch (error) { $('chatLog').insertAdjacentHTML('beforeend', `<div class="bubble assistant error">${escapeHtml(error.message)}</div>`); }
  $('chatLog').scrollTop = $('chatLog').scrollHeight;
 };

if (token) request('/auth/me').then(showApp).catch(() => { localStorage.removeItem('campus_token'); });
