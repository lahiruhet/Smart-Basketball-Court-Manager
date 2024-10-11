from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route('/reservations', methods=['GET'])
def get_reservations():
    # Sample data similar to what you want to return
    reservations_data = {"reservations":{"05:30":["Half Court A"],"06:30":["Half Court B",],"07:30":["Half Court B.","Half Court A."],"08:30":["Full Court"],"09:30":["Full Court"],"10:30":["Full Court"],"11:30":["Full Court"],"12:30":["Full Court"],"13:30":["Full Court"],"14:30":["Full Court"],"15:30":["Full Court"],"16:30":["Full Court"],"17:30":["Full Court"],"18:30":["Half Court A.","Half Court B."],"19:30":["Half Court A.","Half Court B."],"20:30":["Half Court B."],"21:30":["Full Court"]},"last_updated":"2024-09-01 02:52:29"}
    
    return jsonify(reservations_data)

if __name__ == '__main__':
    app.run(debug=True)

