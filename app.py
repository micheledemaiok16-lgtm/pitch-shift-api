from flask import Flask, request, jsonify
import subprocess, tempfile, os, urllib.request, traceback
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
    try:
        print(f"Content-Type: {request.content_type}")
        print(f"Cloudinary cloud: {os.environ.get('CLOUDINARY_CLOUD_NAME')}")
        print(f"Cloudinary key set: {bool(os.environ.get('CLOUDINARY_API_KEY'))}")
        print(f"Cloudinary secret set: {bool(os.environ.get('CLOUDINARY_API_SECRET'))}")

        if request.content_type and 'multipart/form-data' in request.content_type:
            file = request.files['file']
            semitoni = float(request.form.get('semitoni', 2))
            tempo_factor = float(request.form.get('tempo', 1.0))
            inp = tempfile.NamedTemporaryFile(suffix='.m4a', delete=False)
            file.save(inp.name)
            inp_name = inp.name
            inp.close()
        elif request.content_type and 'application/octet-stream' in request.content_type:
            semitoni = float(request.args.get('semitoni', 2))
            tempo_factor = float(request.args.get('tempo', 1.0))
            inp = tempfile.NamedTemporaryFile(suffix='.m4a', delete=False)
            inp.write(request.data)
            inp.close()
            inp_name = inp.name
        else:
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

        af_filters = f'rubberband=pitch={pitch_factor}'
        if tempo_factor != 1.0:
            af_filters += f',atempo={tempo_factor}'

        subprocess.run(
            ['ffmpeg', '-i', inp_name, '-af', af_filters,
             '-codec:a', 'libmp3lame', '-q:a', '2', out, '-y'],
            check=True, capture_output=True
        )
        os.unlink(inp_name)

        try:
            upload_result = cloudinary.uploader.upload(
                out, resource_type='video', format='mp3'
            )
        except Exception as cloud_err:
            os.unlink(out)
            return jsonify({
                'stage': 'cloudinary_upload',
                'error': str(cloud_err),
                'type': type(cloud_err).__name__
            }), 500

        os.unlink(out)
        return jsonify({'url': upload_result['secure_url']})

    except Exception as e:
        return jsonify({
            'stage': 'general',
            'error': str(e),
            'type': type(e).__name__,
            'trace': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
