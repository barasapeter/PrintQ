from pathlib import Path
from datetime import datetime
import humanize
from fastapi.templating import Jinja2Templates

APP_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = APP_DIR / "static"
TEMPLATES_DIR = APP_DIR / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def get_file_icon(filename):
    if not filename:
        return ""

    ext = filename.split(".")[-1].lower() if "." in filename else ""

    if ext == "pdf":
        return '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 4C4 2.89543 4.89543 2 6 2H14L20 8V20C20 21.1046 19.1046 22 18 22H6C4.89543 22 4 21.1046 4 20V4Z" fill="#E53935" stroke="#E53935" stroke-width="1.5"/><path d="M14 2V8H20" fill="#E53935"/><path d="M14 2V8H20" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><text x="8" y="17" font-size="7" font-weight="bold" fill="white" font-family="Arial">PDF</text></svg>'

    if ext in ["doc", "docx"]:
        return '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 4C4 2.89543 4.89543 2 6 2H14L20 8V20C20 21.1046 19.1046 22 18 22H6C4.89543 22 4 21.1046 4 20V4Z" fill="#1E88E5" stroke="#1E88E5" stroke-width="1.5"/><path d="M14 2V8H20" fill="#1E88E5"/><path d="M14 2V8H20" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><text x="6" y="17" font-size="6.5" font-weight="bold" fill="white" font-family="Arial">DOC</text></svg>'

    if ext in ["xls", "xlsx"]:
        return '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 4C4 2.89543 4.89543 2 6 2H14L20 8V20C20 21.1046 19.1046 22 18 22H6C4.89543 22 4 21.1046 4 20V4Z" fill="#43A047" stroke="#43A047" stroke-width="1.5"/><path d="M14 2V8H20" fill="#43A047"/><path d="M14 2V8H20" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><text x="6" y="17" font-size="6.5" font-weight="bold" fill="white" font-family="Arial">XLS</text></svg>'

    if ext in ["ppt", "pptx"]:
        return '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 4C4 2.89543 4.89543 2 6 2H14L20 8V20C20 21.1046 19.1046 22 18 22H6C4.89543 22 4 21.1046 4 20V4Z" fill="#FB8C00" stroke="#FB8C00" stroke-width="1.5"/><path d="M14 2V8H20" fill="#FB8C00"/><path d="M14 2V8H20" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><text x="6.5" y="17" font-size="6" font-weight="bold" fill="white" font-family="Arial">PPT</text></svg>'

    if ext in ["jpg", "jpeg", "png", "gif", "webp", "bmp"]:
        return '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 4C4 2.89543 4.89543 2 6 2H14L20 8V20C20 21.1046 19.1046 22 18 22H6C4.89543 22 4 21.1046 4 20V4Z" fill="#8E24AA" stroke="#8E24AA" stroke-width="1.5"/><path d="M14 2V8H20" fill="#8E24AA"/><path d="M14 2V8H20" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="9" cy="10" r="1.5" fill="white"/><path d="M17 16L14 13L9 17L7 15L4 18" stroke="white" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>'

    if ext == "txt":
        return '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 4C4 2.89543 4.89543 2 6 2H14L20 8V20C20 21.1046 19.1046 22 18 22H6C4.89543 22 4 21.1046 4 20V4Z" fill="#757575" stroke="#757575" stroke-width="1.5"/><path d="M14 2V8H20" fill="#757575"/><path d="M14 2V8H20" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><line x1="7" y1="12" x2="15" y2="12" stroke="white" stroke-width="1.2" stroke-linecap="round"/><line x1="7" y1="15" x2="13" y2="15" stroke="white" stroke-width="1.2" stroke-linecap="round"/><line x1="7" y1="18" x2="11" y2="18" stroke="white" stroke-width="1.2" stroke-linecap="round"/></svg>'

    if ext == "csv":
        return '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 4C4 2.89543 4.89543 2 6 2H14L20 8V20C20 21.1046 19.1046 22 18 22H6C4.89543 22 4 21.1046 4 20V4Z" fill="#2E7D32" stroke="#2E7D32" stroke-width="1.5"/><path d="M14 2V8H20" fill="#2E7D32"/><path d="M14 2V8H20" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><text x="6" y="17" font-size="6.5" font-weight="bold" fill="white" font-family="Arial">CSV</text></svg>'

    return '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 4C4 2.89543 4.89543 2 6 2H14L20 8V20C20 21.1046 19.1046 22 18 22H6C4.89543 22 4 21.1046 4 20V4Z" fill="#607D8B" stroke="#607D8B" stroke-width="1.5"/><path d="M14 2V8H20" fill="#607D8B"/><path d="M14 2V8H20" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M9 14L11 16L15 12" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>'


def format_file_size(bytes_value):
    if not bytes_value:
        return "0 B"
    try:
        bytes_int = int(bytes_value)
    except (ValueError, TypeError):
        return "0 B"

    if bytes_int < 1024:
        return f"{bytes_int} B"
    if bytes_int < 1024 * 1024:
        return f"{(bytes_int / 1024):.1f} KB"
    return f"{(bytes_int / (1024 * 1024)):.1f} MB"


def time_ago(dt):
    if not dt:
        return ""

    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return ""

    if not isinstance(dt, datetime):
        return ""

    now = datetime.now()
    if dt.tzinfo is not None:
        import pytz

        now = datetime.now(pytz.UTC)
        dt = dt.astimezone(pytz.UTC)

    delta = now - dt
    return humanize.naturaltime(delta)


templates.env.filters["get_file_icon"] = get_file_icon
templates.env.filters["format_file_size"] = format_file_size
templates.env.filters["time_ago"] = time_ago
