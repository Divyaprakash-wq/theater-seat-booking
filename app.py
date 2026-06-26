from flask import Flask, render_template, request, redirect, url_for
import random
from datetime import datetime
# Twilio client import karna
from twilio.rest import Client

app = Flask(__name__)

booked_tickets = {}

# --- TWILIO CONFIGURATION ---
# (Twilio.com par register karke yeh details milti hain)
TWILIO_ACCOUNT_SID = 'YOUR_ACCOUNT_SID_HERE'
TWILIO_AUTH_TOKEN = 'YOUR_AUTH_TOKEN_HERE'
TWILIO_PHONE_NUMBER = 'YOUR_TWILIO_NUMBER_HERE' # Jaise '+1234567890'

def send_sms_ticket(to_number, ticket_info):
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Ek badhiya sa Fauji Pass format text message taiyar karna
        message_body = (
            f"🎖️ SAINIK CINEMA PASS 🎖️\n\n"
            f"Pass ID: {ticket_info['ticket_id']}\n"
            f"Name: {ticket_info['booked_by']}\n"
            f"Date: {ticket_info['booking_date']}\n"
            f"Show: {ticket_info['show_time']}\n"
            f"Category: {ticket_info['category']}\n"
            f"Seat: Row {ticket_info['row']}, Seat {ticket_info['seat']}\n\n"
            f"Gate Entry Status: APPROVED. Kisi print ki zaroorat nahi hai, yeh SMS gate par dikhayein."
        )
        
        # Agar number me +91 nahi laga hai, toh jod dena (India ke liye)
        if not to_number.startswith('+'):
            to_number = '+91' + to_number
            
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=to_number
        )
        print(f"SMS successfully sent! SID: {message.sid}")
    except Exception as e:
        print(f"SMS bhejne me error aaya: {e}")

# ----------------------------

def get_category(row):
    if row <= 5: return "OFFRs"
    elif row <= 10: return "JCOs"
    else: return "ORs"

@app.route('/')
def index():
    selected_date = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))
    selected_time = request.args.get('time', '12:00 PM (Morning Show)')
    
    current_layout = {}
    for row in range(1, 26):
        category = get_category(row)
        current_layout[row] = {
            "category": category,
            "seats": {}
        }
        for seat_num in range(1, 15):
            booking_key = f"{selected_date}_{selected_time}_{row}_{seat_num}"
            
            if booking_key in booked_tickets:
                current_layout[row]["seats"][seat_num] = {
                    "status": "booked",
                    "details": booked_tickets[booking_key]
                }
            else:
                current_layout[row]["seats"][seat_num] = {
                    "status": "available"
                }
                
    return render_template('index.html', theater=current_layout, sel_date=selected_date, sel_time=selected_time)

@app.route('/book', methods=['POST'])
def book_seat():
    row = int(request.form.get('row'))
    seat = int(request.form.get('seat'))
    name = request.form.get('customer_name')
    phone = request.form.get('customer_phone')
    b_date = request.form.get('booking_date')  
    s_time = request.form.get('show_time')      
    
    booking_key = f"{b_date}_{s_time}_{row}_{seat}"
    
    if booking_key not in booked_tickets:
        tkt_id = f"TKT-{random.randint(10000, 99999)}"
        
        # Ticket details map me save ki
        ticket_data = {
            "ticket_id": tkt_id,
            "booked_by": name,
            "phone": phone,
            "booking_date": b_date,
            "show_time": s_time,
            "row": row,
            "seat": seat,
            "category": get_category(row)
        }
        booked_tickets[booking_key] = ticket_data
        
        # NAYA: Jaise hi database me booking pakki hui, automatic phone par SMS chala jayega
        send_sms_ticket(phone, ticket_data)
        
        return redirect(url_for('show_ticket', key=booking_key))
        
    return redirect(url_for('index', date=b_date, time=s_time))

@app.route('/ticket/<key>')
def show_ticket(key):
    info = booked_tickets.get(key)
    if info:
        return render_template('ticket.html', row=info['row'], seat=info['seat'], category=info['category'], info=info)
    return "Ticket Not Found", 404

if __name__ == '__main__':
    app.run(debug=True)