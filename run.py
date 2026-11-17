if __name__ == '__main__':
    try:
        from app.main import main
        result = main()
    except Exception:
        import os
        import traceback
        from pathlib import Path
        location = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'LogiZ407ControlPro'
        location.mkdir(parents=True, exist_ok=True)
        (location / 'startup-error.log').write_text(traceback.format_exc(), encoding='utf-8')
        result = 1
    raise SystemExit(result)
