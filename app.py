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
    # --- Ricevi il file: binario diretto O JSON con url ---
    if request.content_type and 'multipart/form-data' in request.content_type:
        # File inviato come form-data (upload binario da n8n)
        file = request.files['file']
        semitoni = float(request.form.get('semitoni', 2))
        tempo_factor = float(request.form.get('tempo', 1.0))
        inp = tempfile.NamedTemporaryFile(suffix='.m4a', delete=False)
        file.save(inp.name)
        inp_name = inp.name
        inp.close()
    elif request.content_type and 'application/octet-stream' in request.content_type:
        # File inviato come body binario puro (n8n binary mode)
        semitoni = float(request.args.get('semitoni', 2))
        tempo_factor = float(request.args.get('tempo', 1.0))
        inp = tempfile.NamedTemporaryFile(suffix='.m4a', delete=False)
        inp.write(request.data)
        inp.close()
        inp_name = inp.name
    else:
        # JSON classico con url
        data = request.get_json()
        url = data['url']
        semitoni = float(data.get('semitoni', 2))
        tempo_factor = float(data.get('tempo', 1.0))
        inp = tempfile.NamedTemporaryFile(suffix='.m4a', delete=False)
        urllib.request.urlretrieve(url, inp.name)
        inp_name = inp.name
        inp.close()

    pitch_factor = 2 ** (semitoni / 12)
    out = inp_name.replace('.m4a', '_out.mp3')

    subprocess.run([
        'ffmpeg', '-i', inp_name, '-af',
        f'rubberband=pitch={pitch_factor}:tempo={tempo_factor}',
        '-codec:a', 'libmp3lame', '-q:a', '2',
        out, '-y'
    ], check=True)

    os.unlink(inp_name)

    upload_result = cloudinary.uploader.upload(
        out,
        resource_type='video',
        format='mp3'
    )
    os.unlink(out)

    return jsonify({'url': upload_result['secure_url']})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
