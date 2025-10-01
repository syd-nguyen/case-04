from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import ValidationError
from models import SurveySubmission, StoredSurveyRecord
from storage import append_json_line
from hashlib import sha256 # added for exercises 2 and 3

app = Flask(__name__)
# Allow cross-origin requests so the static HTML can POST from localhost or file://
CORS(app, resources={r"/v1/*": {"origins": "*"}})

@app.route("/ping", methods=["GET"])
def ping():
    """Simple health check endpoint."""
    return jsonify({
        "status": "ok",
        "message": "API is alive",
        "utc_time": datetime.now(timezone.utc).isoformat()
    })

@app.post("/v1/survey")
def submit_survey():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "invalid_json", "detail": "Body must be application/json"}), 400

    try:
        submission = SurveySubmission(**payload)
    except ValidationError as ve:
        return jsonify({"error": "validation_error", "detail": ve.errors()}), 422

    record = StoredSurveyRecord(
        **submission.dict(),
        received_at=datetime.now(timezone.utc),
        ip=request.headers.get("X-Forwarded-For", request.remote_addr or ""),
    )

    recordDict = record.dict()

    # exercise 3. add a new submission_id field, with the default as sha256(email + YYYYMMDDHH)
    if(recordDict['submission_id'] == 'none'):
        recAt = str(recordDict['received_at'])
        time = recAt[:4] + recAt[5:7] + recAt[8:10] + recAt[11:13]
        recordDict['submission_id'] = hash(recordDict['email'] + time)

    # exercise 2. hash the email and age fields
    # this is after exercise 3 because exercise 3 uses the unhashed email
    recordDict['email'] = hash(recordDict['email'])
    recordDict['age'] = hash(str(recordDict['age']))    

    append_json_line(recordDict) # changed from record.dict()
    return jsonify({"status": "ok"}), 201

# added for exercises 2 and 3    
def hash(str):
    return sha256(str.encode('utf-8')).hexdigest()

if __name__ == "__main__":
    app.run(port=0, debug=True)
