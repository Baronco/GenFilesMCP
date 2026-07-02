"""Shared helpers used across all API route modules."""

from html import escape

from fastapi import Request
from fastapi.responses import HTMLResponse


def build_request_context(request: Request) -> dict[str, dict[str, str]]:
    """Build a request context dict from FastAPI Request headers."""
    return {"headers": dict(request.headers)}


def get_file_icon_svg(file_type: str) -> str:
    """Return an inline SVG icon for the given file type."""
    file_type_normalized = (file_type or "").strip().lower()
    color_map = {
        "pdf": "#ef4444",
        "docx": "#60a5fa",
        "pptx": "#fb923c",
        "xlsx": "#22c55e",
        "md": "#7c3aed",
    }
    icon_label_map = {
        "pdf": "PDF",
        "docx": "DOCX",
        "pptx": "PPTX",
        "xlsx": "XLSX",
        "md": "MD",
    }

    icon_label = icon_label_map.get(file_type_normalized, "FILE")
    icon_fill = color_map.get(file_type_normalized, "#6b7280")
    is_long_label = len(icon_label) > 3
    font_size = "8.5" if is_long_label else "12"
    text_attrs = ' textLength="26" lengthAdjust="spacingAndGlyphs"' if is_long_label else ""

    svg = (
        '<svg viewBox="0 0 42 32" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" role="img" style="width:32px;height:26px;">'
        f'<rect x="2" y="2" width="38" height="28" rx="6" fill="{icon_fill}" />'
        '<path d="M8 7h11l4 4v12a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2Z" fill="#ffffff" fill-opacity="0.12" />'
        f'<text x="21" y="18" text-anchor="middle" dominant-baseline="middle" font-family="Inter, Arial, sans-serif" font-size="{font_size}" font-weight="700" fill="#ffffff"{text_attrs}>{icon_label}</text>'
        '</svg>'
    )
    return svg


def render_download_button_html(result: dict) -> HTMLResponse | None:
    """Return an HTMLResponse with a download button for generated file results."""
    if not isinstance(result, dict):
        return None

    download_url = result.get("download_url")
    file_name = result.get("file_name")
    file_type = result.get("file_type")

    if not download_url or not file_name or not file_type:
        return None

    safe_url = escape(download_url, quote=True)
    safe_name = escape(file_name)
    safe_type = escape(file_type)
    if safe_name.lower().endswith(f".{safe_type.lower()}"):
        safe_download_name = safe_name
    else:
        safe_download_name = f"{safe_name}.{safe_type}"
    display_name = escape(safe_download_name)

    html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Download file</title>
    <style>
        * {{ box-sizing: border-box; }}
        html, body {{ margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: radial-gradient(circle at top, rgba(37, 99, 235, 0.15), transparent 36%),
                        linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
            color: #111827;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 24px;
        }}
        .download-card {{
            width: min(100%, 420px);
            padding: 18px 18px 16px;
            background: rgba(255, 255, 255, 0.98);
            border: 1px solid rgba(148, 163, 184, 0.20);
            border-radius: 24px;
            box-shadow: 0 18px 42px rgba(15, 23, 42, 0.12);
            text-align: center;
            backdrop-filter: blur(14px);
        }}
        .download-card h1 {{
            font-size: 1.14rem;
            margin: 0 0 14px;
            line-height: 1.25;
            letter-spacing: -0.02em;
        }}
        .download-button {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.65rem;
            width: 100%;
            padding: 10px 16px;
            color: #ffffff;
            background: linear-gradient(135deg, #2563eb 0%, #4338ca 100%);
            border-radius: 16px;
            text-decoration: none;
            font-weight: 700;
            font-size: 0.96rem;
            transition: transform 0.16s ease, box-shadow 0.16s ease;
            box-shadow: 0 10px 24px rgba(37, 99, 235, 0.18);
        }}
        .download-button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 12px 26px rgba(37, 99, 235, 0.22);
        }}
        .download-button:active {{
            transform: translateY(0);
        }}
        .download-icon {{
            width: 28px;
            height: 28px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }}
        .file-name {{
            margin: 12px auto 0;
            color: #475569;
            font-size: 0.86rem;
            line-height: 1.4;
            word-break: break-word;
            max-width: 100%;
            opacity: 0.88;
        }}
    </style>
</head>
<body>
    <main class=\"download-card\">
        <h1>Your file is ready to download</h1>
        <a class=\"download-button\" href=\"{safe_url}\" target=\"_blank\" rel=\"noopener noreferrer\" download=\"{safe_download_name}\" aria-label=\"Download {display_name}\">
            <span class="download-icon">{get_file_icon_svg(safe_type)}</span>
            Download file
        </a>
        <div class=\"file-name\">{display_name}</div>
    </main>
    <script>
        function reportHeight() {{
            const h = document.documentElement.scrollHeight;
            parent.postMessage({{ type: 'iframe:height', height: h }}, '*');
        }}
        window.addEventListener('load', reportHeight);
        if (typeof ResizeObserver !== 'undefined') {{
            new ResizeObserver(reportHeight).observe(document.body);
        }} else {{
            window.addEventListener('resize', reportHeight);
        }}
    </script>
</body>
</html>"""

    return HTMLResponse(content=html, headers={"Content-Disposition": "inline", "Content-Type": "text/html"})


def extract_files_from_chat(chat_data: dict) -> list:
    """Extract file references (id + name) from an Open WebUI chat history dict."""
    files = []
    history = chat_data.get("chat", {}).get("history", {})
    messages = history.get("messages", {})

    for message_id, message in messages.items():
        message_files = message.get("files", [])
        for file_info in message_files:
            files.append({
                "file_id": file_info.get("id"),
                "file_name": file_info.get("name"),
            })

    return files
