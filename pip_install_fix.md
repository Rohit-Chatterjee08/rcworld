# PyPI Connection Timeout Fix

You're experiencing connection timeout issues when trying to install Flask from PyPI. Here are several solutions to resolve this:

## Solution 1: Increase pip timeout
```bash
pip install --timeout=120 -r requirements.txt
```

## Solution 2: Use a different PyPI mirror
```bash
pip install -i https://pypi.python.org/simple/ -r requirements.txt
```

## Solution 3: Use pip with retries and longer timeout
```bash
pip install --retries 5 --timeout=120 -r requirements.txt
```

## Solution 4: Install packages individually with timeout
```bash
pip install --timeout=120 Flask
pip install --timeout=120 -r requirements.txt
```

## Solution 5: Use conda instead of pip (if available)
```bash
conda install flask
```

## Solution 6: Configure pip to use a more reliable index
Create/edit `~/.pip/pip.conf` (Linux/Mac) or `%APPDATA%\pip\pip.ini` (Windows):
```ini
[global]
timeout = 120
retries = 5
index-url = https://pypi.python.org/simple/
trusted-host = pypi.python.org
```

## Solution 7: Use pip with no-cache-dir
```bash
pip install --no-cache-dir --timeout=120 -r requirements.txt
```

## Solution 8: Manual download and install
If all else fails, you can download the wheel files manually:
1. Go to https://pypi.org/project/Flask/#files
2. Download the appropriate wheel file
3. Install locally: `pip install path/to/flask-wheel-file.whl`

## Recommended Quick Fix
Try this command first:
```bash
pip install --timeout=120 --retries 5 --no-cache-dir -r requirements.txt
```

## Network-specific issues
If you're behind a corporate firewall or proxy, you might need to configure pip to use your proxy settings:
```bash
pip install --proxy http://user:password@proxy.server:port -r requirements.txt
```

Choose the solution that works best for your network environment.