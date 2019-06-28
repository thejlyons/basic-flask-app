from app import app
import app.tools as tools
from flask import render_template


@app.route('/')
@app.route('/index')
def index():
    """Home."""
    tools.test_tools("Tools works!")
    return render_template('index/index.html')
