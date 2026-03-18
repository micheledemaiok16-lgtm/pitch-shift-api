from flask import Flask, request, send_file
import subprocess, tempfile, os

app = Flask(__name__)

@app.route('/pitch', methods=['POST'])
def pitch():
    f = request.files['audio']
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as inp:
        f.save(inp.name)
        out = inp.name.replace('.mp3', '_out.mp3')
    subprocess.run(['ffmpeg', '-i', inp.name, '-af',
                    'rubberband=pitch=1.1225', out, '-y'])
    os.unlink(inp.name)
    return send_file(out, mimetype='audio/mpeg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
```

**`requirements.txt`**
```
flask