from flask import Flask, request, send_file
import subprocess, tempfile, os, urllib.request

app = Flask(__name__)

@app.route('/pitch', methods=['POST'])
def pitch():
    data = request.get_json()
    url = data['url']
    
    with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as inp:
        urllib.request.urlretrieve(url, inp.name)
        out = inp.name.replace('.m4a', '_out.m4a')
    
    subprocess.run(['ffmpeg', '-i', inp.name, '-af',
                    'rubberband=pitch=1.1225', out, '-y'])
    os.unlink(inp.name)
    return send_file(out, mimetype='audio/mp4')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))