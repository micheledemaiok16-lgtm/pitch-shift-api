from flask import Flask, request, jsonify
import subprocess, tempfile, os, urllib.request
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

@app.route('/pitch', methods=['POST'])
def pitch():
    data = request.get_json()
    url = data['url']
    semitoni = data.get('semitoni', 2)
    pitch_factor = 2 ** (semitoni / 12)

    with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as inp:
        urllib.request.urlretrieve(url, inp.name)
        inp_name = inp.name

    out = inp_name.replace('.m4a', '_out.m4a')
    subprocess.run(['ffmpeg', '-i', inp_name, '-af',
                    f'rubberband=pitch={pitch_factor}:tempo=1.1',
                    out, '-y'])
    os.unlink(inp_name)

    upload_result = cloudinary.uploader.upload(out,
        resource_type='video',
        format='m4a'
    )
    os.unlink(out)

    return jsonify({'url': upload_result['secure_url']})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
