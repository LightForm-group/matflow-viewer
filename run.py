import threading
import webbrowser
import os

from matflow_viewer import app


def main():
    port = 5000
    url = "http://127.0.0.1:{0}".format(port)

    if 'WERKZEUG_RUN_MAIN' not in os.environ:
        threading.Timer(2, lambda: webbrowser.open(url)).start()

    app.secret_key = 'super secret key'
    app.run(port=port)


if __name__ == '__main__':
    main()
