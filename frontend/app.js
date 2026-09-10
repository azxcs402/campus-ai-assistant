const API = 'http://127.0.0.1:8000/api/v1';
const PROVIDERS_KEY = 'campus_api_providers';
let token = localStorage.getItem('campus_token');
let conversationId = null;
let currentUser = null;
let courses = [];
let tasks = [];
let editingTaskId = null;
let providers = loadProviders();
let activeProviderId = localStorage.getItem('campus_active_provider') || '';

const $ = (id) => document.getElementById(id);
function escapeHtml(value) { return String(value ?? '').replace(/[&<>'"]/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' }[c])); }
function loadProviders() { try { return JSON.parse(localStorage.getItem(PROVIDERS_KEY) || '[]'); } catch { return []; } }
function persistProviders() { localStorage.setItem(PROVIDERS_KEY, JSON.stringify(providers)); }
function activeProvider() { return providers.find(provider => provider.id === activeProviderId) || null; }
function formatDate(value) { return value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '无截止日期'; }
function dateInputValue(value) { return value ? value.slice(0, 10) : ''; }

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
  if (!response.ok) {
    const detail = body?.detail;
    const message = Array.isArray(detail) ? detail.map(item => item.msg).join('；') : detail;
    throw new Error(message || body?.message || '请求失败');
  }
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

function renderProviders() {
  const select = $('providerSelect');
  if (!select) return;
  select.innerHTML = `<option value="">环境变量 / 演示模式</option>${providers.map(provider => `<option value="${escapeHtml(provider.id)}">${escapeHtml(provider.name)}</option>`).join('')}`;
  select.value = activeProviderId;
  if (select.value !== activeProviderId) activeProviderId = '';
  $('aiStatus').textContent = activeProvider() ? `当前：${activeProvider().name}` : '演示模式可用';
}
function clearProviderForm() { $('providerForm').reset(); $('providerBaseUrl').value = 'https://api.deepseek.com/v1'; $('providerModel').value = 'deepseek-chat'; }

async function showApp(user) {
  currentUser = user;
  $('authView').classList.add('hidden');
  $('appView').classList.remove('hidden');
  const roleNames = { student: '学生', teacher: '教师', admin: '管理员' };
  $('userBox').innerHTML = `<span>${escapeHtml(user.nickname)} · ${roleNames[user.role] || user.role}</span><button class="link-button" id="logoutBtn">退出</button>`;
  $('logoutBtn').onclick = () => { localStorage.removeItem('campus_token'); location.reload(); };
  $('adminPanel').classList.toggle('hidden', user.role !== 'admin');
  renderProviders();
  await loadData();
}

function selectedCourseId() { return Number($('courseSelect').value || $('materialCourseSelect').value || courses[0]?.id || 0); }

function renderCourseOptions(selectedId) {
  const options = courses.map(course => `<option value="${course.id}">${escapeHtml(course.name)}</option>`).join('');
  $('courseSelect').innerHTML = options;
  $('materialCourseSelect').innerHTML = options;
  $('statsCourse').innerHTML = `<option value="">全部课程</option>${options}`;
  const validId = courses.some(course => course.id === Number(selectedId)) ? Number(selectedId) : courses[0]?.id;
  if (validId) {
    $('courseSelect').value = String(validId);
    $('materialCourseSelect').value = String(validId);
  }
}

async function loadData(preferredCourseId = null) {
  try {
    const preservedId = preferredCourseId || selectedCourseId();
    const [loadedCourses, loadedTasks, upcoming, conversations] = await Promise.all([request('/courses'), request('/tasks'), request('/tasks/upcoming'), request('/conversations')]);
    courses = loadedCourses;
    tasks = loadedTasks;
    if (!courses.length) {
      const created = await request('/courses', { method: 'POST', body: JSON.stringify({ name: '系统设计与实践', semester: '2026 秋' }) });
      courses = await request('/courses');
      preferredCourseId = created.id;
    }
    renderCourseOptions(preferredCourseId || preservedId);
    renderTasks(tasks);
    renderUpcoming(upcoming);
    const courseId = selectedCourseId();
    renderMaterials(courseId ? await request(`/courses/${courseId}/materials`) : []);
    await loadStats();
    if (currentUser?.role === 'admin') await loadUsers();
    if (!conversationId) conversationId = conversations[0]?.id || (await request('/conversations', { method: 'POST' })).id;
    renderChat(await request(`/conversations/${conversationId}/messages`));
  } catch (error) { alert(error.message); }
}

function renderStats(data) {
  $('totalStat').textContent = data.total;
  $('doneStat').textContent = data.completed;
  $('overdueStat').textContent = data.overdue;
  $('rateStat').textContent = `${Math.round(data.completion_rate * 100)}%`;
}

async function loadStats() {
  const params = new URLSearchParams();
  if ($('statsCourse').value) params.set('course_id', $('statsCourse').value);
  if ($('statsFrom').value) params.set('from', $('statsFrom').value);
  if ($('statsTo').value) params.set('to', $('statsTo').value);
  const courseParams = new URLSearchParams(params);
  courseParams.delete('course_id');
  const [overview, byCourse] = await Promise.all([
    request(`/stats/overview${params.size ? `?${params}` : ''}`),
    request(`/stats/courses${courseParams.size ? `?${courseParams}` : ''}`),
  ]);
  renderStats(overview);
  renderCourseChart(byCourse);
}

function renderCourseChart(rows) {
  $('courseChart').innerHTML = rows.length ? rows.map(row => `<div class="chart-row"><strong>${escapeHtml(row.course_name)}</strong><div class="chart-track" title="完成率 ${Math.round(row.completion_rate * 100)}%"><div class="chart-bar" style="width:${Math.round(row.completion_rate * 100)}%"></div></div><span class="chart-value">${row.completed}/${row.total} · 逾期 ${row.overdue}</span></div>`).join('') : '<p class="empty">所选时间段暂无课程任务数据。</p>';
}

function renderTasks(items) {
  $('taskList').innerHTML = items.length ? items.map(task => `<article class="task ${task.status === 'done' ? 'completed' : ''}"><div><strong>${escapeHtml(task.title)}</strong><small>${escapeHtml(formatDate(task.due_at))} · ${escapeHtml(task.priority)} · ${escapeHtml(task.course_name)}${task.note ? `<br>备注：${escapeHtml(task.note)}` : ''}</small></div><div class="task-actions"><button data-action="toggle" data-id="${task.id}" data-status="${task.status === 'done' ? 'todo' : 'done'}">${task.status === 'done' ? '恢复' : '完成'}</button><button class="secondary" data-action="edit" data-id="${task.id}">编辑</button><button class="danger" data-action="delete" data-id="${task.id}">删除</button></div></article>`).join('') : '<p class="empty">还没有任务，添加第一个学习任务吧。</p>';
  document.querySelectorAll('[data-action="toggle"]').forEach(button => button.onclick = async () => {
    try { await withBusy(button, () => request(`/tasks/${button.dataset.id}`, { method: 'PATCH', body: JSON.stringify({ status: button.dataset.status }) })); await loadData(); }
    catch (error) { alert(error.message); }
  });
  document.querySelectorAll('[data-action="edit"]').forEach(button => button.onclick = () => beginTaskEdit(Number(button.dataset.id)));
  document.querySelectorAll('[data-action="delete"]').forEach(button => button.onclick = async () => {
    if (!confirm('确认删除这个任务吗？')) return;
    try { await withBusy(button, () => request(`/tasks/${button.dataset.id}`, { method: 'DELETE' })); cancelTaskEdit(); await loadData(); }
    catch (error) { alert(error.message); }
  });
}

function beginTaskEdit(taskId) {
  const task = tasks.find(item => item.id === taskId);
  if (!task) return;
  editingTaskId = taskId;
  $('taskTitle').value = task.title;
  $('courseSelect').value = String(task.course_id);
  $('dueAt').value = dateInputValue(task.due_at);
  $('priority').value = task.priority;
  $('taskNote').value = task.note || '';
  $('taskSubmitBtn').textContent = '保存修改';
  $('taskCancelBtn').classList.remove('hidden');
  $('taskTitle').focus();
}

function cancelTaskEdit() {
  editingTaskId = null;
  $('taskForm').reset();
  $('priority').value = 'medium';
  $('taskSubmitBtn').textContent = '添加任务';
  $('taskCancelBtn').classList.add('hidden');
}

function renderUpcoming(items) {
  $('upcomingList').innerHTML = items.length ? `<div class="upcoming-title">即将截止</div>${items.slice(0, 3).map(task => `<div class="upcoming-item ${task.urgent ? 'urgent' : ''}"><span>${escapeHtml(task.title)}</span><small>${task.remaining_hours <= 0 ? '已逾期' : `${task.remaining_hours} 小时内`}</small></div>`).join('')}` : '';
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

async function openCourseManager() {
  const courseId = selectedCourseId();
  if (!courseId) return;
  try {
    const course = await request(`/courses/${courseId}`);
    $('courseName').value = course.name;
    $('courseSemester').value = course.semester || '';
    $('courseMeta').textContent = `任务 ${course.task_count} 项 · 资料 ${course.material_count} 份 · 课程编号 ${course.id}`;
    $('courseForm').classList.remove('hidden');
  } catch (error) { alert(error.message); }
}

async function loadUsers() {
  const users = await request('/users');
  $('userList').innerHTML = users.map(user => `<div class="user-row"><strong>${escapeHtml(user.nickname)}</strong><span>${escapeHtml(user.account)}</span><select data-role-user="${user.id}" ${user.id === currentUser.id ? 'disabled' : ''}><option value="student" ${user.role === 'student' ? 'selected' : ''}>学生</option><option value="teacher" ${user.role === 'teacher' ? 'selected' : ''}>教师</option><option value="admin" ${user.role === 'admin' ? 'selected' : ''}>管理员</option></select></div>`).join('');
  document.querySelectorAll('[data-role-user]').forEach(select => select.onchange = async () => {
    try { await request(`/users/${select.dataset.roleUser}/role`, { method: 'PATCH', body: JSON.stringify({ role: select.value }) }); }
    catch (error) { alert(error.message); await loadUsers(); }
  });
}

$('authForm').onsubmit = async (event) => { event.preventDefault(); try { const result = await request('/auth/login', { method: 'POST', body: JSON.stringify({ account: $('account').value, password: $('password').value }) }); token = result.token; localStorage.setItem('campus_token', token); await showApp(result.user); } catch (error) { $('authError').textContent = error.message; } };
$('registerBtn').onclick = async () => { try { if (!$('nickname').value) throw new Error('注册时请填写昵称'); const result = await request('/auth/register', { method: 'POST', body: JSON.stringify({ account: $('account').value, password: $('password').value, nickname: $('nickname').value }) }); token = result.token; localStorage.setItem('campus_token', token); await showApp(result.user); } catch (error) { $('authError').textContent = error.message; } };
$('taskForm').onsubmit = async (event) => {
  event.preventDefault();
  const payload = { title: $('taskTitle').value.trim(), course_id: Number($('courseSelect').value), due_at: $('dueAt').value || null, priority: $('priority').value, note: $('taskNote').value.trim() || null };
  try {
    await withBusy(event.submitter, () => request(editingTaskId ? `/tasks/${editingTaskId}` : '/tasks', { method: editingTaskId ? 'PATCH' : 'POST', body: JSON.stringify(payload) }));
    cancelTaskEdit(); await loadData(payload.course_id);
  } catch (error) { alert(error.message); }
};
$('taskCancelBtn').onclick = cancelTaskEdit;
$('refreshBtn').onclick = () => loadData();
$('courseSelect').onchange = () => { if (!editingTaskId) $('materialCourseSelect').value = $('courseSelect').value; };
$('createCourseBtn').onclick = async () => {
  const name = prompt('请输入课程名称');
  if (name === null) return;
  const trimmedName = name.trim();
  if (!trimmedName) { alert('课程名称不能为空'); return; }
  const semester = prompt('请输入学期（可选，例如：2026 秋）');
  try { const course = await withBusy($('createCourseBtn'), () => request('/courses', { method: 'POST', body: JSON.stringify({ name: trimmedName, semester: semester?.trim() || null }) })); await loadData(course.id); }
  catch (error) { alert(error.message); }
};
$('manageCourseBtn').onclick = openCourseManager;
$('courseCancelBtn').onclick = () => $('courseForm').classList.add('hidden');
$('courseForm').onsubmit = async (event) => {
  event.preventDefault();
  const courseId = selectedCourseId();
  try { await withBusy(event.submitter, () => request(`/courses/${courseId}`, { method: 'PATCH', body: JSON.stringify({ name: $('courseName').value.trim(), semester: $('courseSemester').value.trim() || null }) })); $('courseForm').classList.add('hidden'); await loadData(courseId); }
  catch (error) { alert(error.message); }
};
$('courseDeleteBtn').onclick = async () => {
  const courseId = selectedCourseId();
  if (!confirm('仅空课程可删除。确认删除当前课程吗？')) return;
  try { await withBusy($('courseDeleteBtn'), () => request(`/courses/${courseId}`, { method: 'DELETE' })); $('courseForm').classList.add('hidden'); await loadData(); }
  catch (error) { alert(error.message); }
};
$('materialCourseSelect').onchange = async () => { try { await loadMaterials($('materialCourseSelect').value); } catch (error) { alert(error.message); } };
async function loadMaterials(courseId) { renderMaterials(await request(`/courses/${courseId}/materials`)); }
$('materialForm').onsubmit = async (event) => {
  event.preventDefault();
  const courseId = $('materialCourseSelect').value;
  const file = $('materialFile').files[0];
  if (!file) return;
  const data = new FormData(); data.append('course_id', courseId); data.append('file', file);
  if ($('materialTitle').value.trim()) data.append('title', $('materialTitle').value.trim());
  try { await withBusy(event.submitter, () => request('/materials', { method: 'POST', body: data })); event.target.reset(); await loadData(Number(courseId)); }
  catch (error) { alert(error.message); }
};
$('statsForm').onsubmit = async (event) => { event.preventDefault(); try { await withBusy(event.submitter, loadStats); } catch (error) { alert(error.message); } };
$('statsResetBtn').onclick = async () => { $('statsForm').reset(); try { await loadStats(); } catch (error) { alert(error.message); } };
$('providerSelect').onchange = (event) => { activeProviderId = event.target.value; localStorage.setItem('campus_active_provider', activeProviderId); renderProviders(); };
$('providerManageBtn').onclick = () => { const form = $('providerForm'); form.classList.toggle('hidden'); if (!form.classList.contains('hidden')) { const current = activeProvider(); if (current) { $('providerName').value = current.name; $('providerBaseUrl').value = current.base_url; $('providerModel').value = current.model; $('providerApiKey').value = current.api_key; } else clearProviderForm(); } };
$('providerCancelBtn').onclick = () => { $('providerForm').classList.add('hidden'); clearProviderForm(); };
$('providerDeleteBtn').onclick = () => { if (!activeProvider()) { alert('当前未选择自定义 API'); return; } if (!confirm(`确认删除“${activeProvider().name}”吗？`)) return; providers = providers.filter(provider => provider.id !== activeProviderId); activeProviderId = ''; persistProviders(); localStorage.setItem('campus_active_provider', ''); renderProviders(); $('providerForm').classList.add('hidden'); clearProviderForm(); };
$('providerForm').onsubmit = (event) => { event.preventDefault(); const name = $('providerName').value.trim(); const baseUrl = $('providerBaseUrl').value.trim().replace(/\/$/, ''); const model = $('providerModel').value.trim(); const apiKey = $('providerApiKey').value.trim(); if (!name || !model || !apiKey) { alert('请完整填写 API 名称、模型名称和 API Key'); return; } if (!/^https?:\/\//i.test(baseUrl)) { alert('Base URL 必须以 http:// 或 https:// 开头'); return; } const provider = { id: activeProviderId || `provider-${Date.now()}`, name, base_url: baseUrl, model, api_key: apiKey }; const index = providers.findIndex(item => item.id === provider.id); if (index >= 0) providers[index] = provider; else providers.push(provider); activeProviderId = provider.id; persistProviders(); localStorage.setItem('campus_active_provider', activeProviderId); renderProviders(); $('providerForm').classList.add('hidden'); clearProviderForm(); };
$('chatForm').onsubmit = async (event) => { event.preventDefault(); const input = $('chatInput'); const content = input.value.trim(); if (!content || !conversationId) return; input.value = ''; $('chatLog').insertAdjacentHTML('beforeend', `<div class="bubble user">${escapeHtml(content)}</div>`); try { const reply = await withBusy(event.submitter, () => request(`/conversations/${conversationId}/messages`, { method: 'POST', body: JSON.stringify({ content, provider: activeProvider() }) })); $('chatLog').insertAdjacentHTML('beforeend', `<div class="bubble assistant">${escapeHtml(reply.content)}</div>`); } catch (error) { $('chatLog').insertAdjacentHTML('beforeend', `<div class="bubble assistant error">${escapeHtml(error.message)}</div>`); } $('chatLog').scrollTop = $('chatLog').scrollHeight; };

if (token) request('/auth/me').then(showApp).catch(() => { localStorage.removeItem('campus_token'); });
renderProviders();
