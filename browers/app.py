from flask import Flask, request, render_template_string, send_from_directory, abort, session, redirect, url_for
from werkzeug.utils import safe_join
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 请替换为实际的密钥

# 指定根目录
DOWNLOAD_DIRECTORY = "/app/downloads"  # 请替换为实际目录

# 美化后的 HTML 模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Browser</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        header {
            background-color: #3f51b5;
            color: white;
            padding: 20px;
            width: 100%;
            text-align: center;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        }
        header h1 {
            margin: 0;
            font-size: 2rem;
        }
        .container {
            display: flex;
            flex-grow: 1;
            width: 100%;
        }
        .sidebar {
            width: 250px;
            background-color: #ffffff;
            padding: 20px;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
            height: 100%;
            overflow-y: auto;
        }
        .sidebar h3 {
            margin-top: 0;
            font-size: 1.2rem;
        }
        .sidebar ul {
            list-style: none;
            padding: 0;
        }
        .sidebar ul li {
            margin-bottom: 10px;
            padding: 8px;
            background: #f9f9f9;
            border-radius: 4px;
            transition: background 0.3s;
        }
        .sidebar ul li a {
            text-decoration: none;
            color: #3f51b5;
            font-weight: bold;
        }
        .sidebar ul li:hover {
            background: #3f51b5;
            color: white;
        }
        .sidebar ul li:hover a {
            color: white;
        }
        .content {
            flex-grow: 1;
            background: white;
            padding: 20px;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            overflow-y: auto;
        }
        .content ul {
            list-style: none;
            padding: 0;
        }
        .content ul li {
            padding: 10px 15px;
            margin: 5px 0;
            background: #f9f9f9;
            border-radius: 4px;
            transition: background 0.3s, color 0.3s;
        }
        .content ul li a {
            text-decoration: none;
            color: #3f51b5;
            font-weight: bold;
            display: block;
        }
        .content ul li:hover {
            background: #3f51b5;
            color: white;
        }
        .content ul li:hover a {
            color: #f4f4f9;  /* 修改为不同的颜色 */
        }
        footer {
            margin-top: 20px;
            text-align: center;
            color: #777;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <header>
        <h1>File Browser</h1>
        <p>Browsing: /{{ current_path }}</p>
    </header>
    <div class="container">
        <!-- 侧边栏 -->
        <div class="sidebar">
            <h3>Directory Navigation</h3>
            <ul>
                <li><a href="/files">Root</a></li>
                {% for folder in path_parts %}
                    <li><a href="/files/{{ folder }}">{{ folder }}</a></li>
                {% endfor %}
            </ul>
            <ul>
                {% for folder in folders %}
                    <li><a href="/files/{{ folder }}">{{ folder }}</a></li>
                {% endfor %}
            </ul>
        </div>

        <!-- 文件列表展示 -->
        <div class="content">
            <h3>Files in Directory:</h3>
            <ul>
                {% for file in files %}
                    <li><span>📄</span><a href="/files/{{ file }}">{{ file }}</a></li>
                {% endfor %}
            </ul>
        </div>
    </div>
    <footer>
        &copy; 2025 File Browser Service - Powered by Flask
    </footer>
</body>
</html>
"""

# 登录页面的 HTML 模板
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .login-container {
            background: white;
            padding: 20px;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
        }
        .login-container h2 {
            margin: 0 0 20px 0;
            font-size: 1.5rem;
            text-align: center;
        }
        .login-container form {
            display: flex;
            flex-direction: column;
        }
        .login-container input[type="password"] {
            padding: 10px;
            margin-bottom: 20px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        .login-container input[type="submit"] {
            padding: 10px;
            background-color: #3f51b5;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .login-container input[type="submit"]:hover {
            background-color: #303f9f;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>Login</h2>
        <form method="post">
            <input type="password" name="password" placeholder="Enter Password" required style="padding: 15px; font-size: 1rem;">
            <input type="submit" value="Login">
        </form>
    </div>
</body>
</html>
"""

# 设置访问密码
ACCESS_PASSWORD = '11223344'  # 请替换为实际的密码

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == ACCESS_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('browse_or_download'))
        else:
            return render_template_string(LOGIN_TEMPLATE, error="Invalid password")
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/files', defaults={'path': ''})
@app.route('/files/<path:path>')
def browse_or_download(path):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    try:
        # 计算完整路径
        full_path = safe_join(DOWNLOAD_DIRECTORY, path)
        
        # 检查路径是否存在
        if not os.path.exists(full_path):
            abort(404, description="Path not found")
        
        # 分解路径部分，供侧边栏显示
        path_parts = path.split('/') if path else []
        
        # 如果是目录，显示目录内容
        if os.path.isdir(full_path):
            # 获取目录内容
            items = os.listdir(full_path)
            folders = [os.path.join(path, item) for item in items if os.path.isdir(safe_join(full_path, item))]
            files = [os.path.join(path, item) for item in items if os.path.isfile(safe_join(full_path, item))]
            return render_template_string(HTML_TEMPLATE, current_path=path or '/', path_parts=path_parts, folders=folders, files=files)
        
        # 如果是文件，提供下载
        elif os.path.isfile(full_path):
            directory = os.path.dirname(full_path)
            filename = os.path.basename(full_path)
            return send_from_directory(directory, filename, as_attachment=True)
        
        else:
            abort(403, description="Unsupported file type")
    except Exception as e:
        abort(400, description=str(e))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
