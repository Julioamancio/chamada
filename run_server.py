from webapp import create_app
import threading
import time
import webbrowser

app = create_app()

def _open_browser():
    # Give the server a moment to start
    time.sleep(1.5)
    url = "http://127.0.0.1:5000/"
    try:
        webbrowser.open(url)
    except Exception:
        pass

if __name__ == "__main__":
    t = threading.Thread(target=_open_browser, daemon=True)
    t.start()
    # Bind to localhost for desktop usage
    app.run(host="127.0.0.1", port=5000, debug=False)
