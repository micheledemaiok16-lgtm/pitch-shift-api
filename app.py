from flask import Flask, request, send_file
import subprocess, tempfile, os, urllib.request

app = Flask(__name__)

@app.route('/pitch', methods=['POST'])
def pitch():
    data = request.get_json()
    url = data['url']
    semitoni = data.get('semitoni', 2)
    
    pitch_factor = 2 ** (semitoni / 12)
    
    with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as inp:
        urllib.request.urlretrieve(url, inp.name)
        out = inp.name.replace('.m4a', '_out.m4a')
    
    subprocess.run(['ffmpeg', '-i', inp.name, '-af',
                    f'rubberband=pitch={pitch_factor}:tempo=1.1',
                    out, '-y'])
    os.unlink(inp.name)
    return send_file(out, mimetype='audio/mp4')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))