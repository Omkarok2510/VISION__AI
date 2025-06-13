import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import logging
import json
import hashlib
import math
# No 'random' import needed as technician data is now fixed

# Configure logging for Flask app
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Placeholder for AI/Blockchain Modules ---
class ComplaintPredictor:
    def __init__(self):
        logger.info("ComplaintPredictor initialized (placeholder).")
    def predict_resolution_time(self, problem_description: str, error_codes: list) -> str:
        # This is a placeholder. A real implementation would use an ML model.
        return "24-48 hours"

class ComplaintLedger:
    def __init__(self):
        self.chain = []
        self.current_complaints = []
        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)
        logger.info("ComplaintLedger initialized.")

    def new_block(self, proof, previous_hash=None):
        """
        Creates a new Block and adds it to the chain.
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.now()),
            'complaints': self.current_complaints,
            'proof': proof,
            'previous_hash': previous_hash or self.hash_block(self.chain[-1]) if self.chain else '1',
        }
        # Reset the current list of complaints
        self.current_complaints = []
        self.chain.append(block)
        return block

    def add_complaint(self, complaint_data: dict) -> str:
        """
        Adds a new complaint to the list of complaints in the current block.
        When enough complaints are accumulated, a new block is mined.
        """
        self.current_complaints.append(complaint_data)
        # For simplicity, we mine a new block immediately after each complaint for now.
        # In a real scenario, you'd batch complaints or mine on a schedule.
        last_block = self.chain[-1]
        proof = self.proof_of_work(last_block['proof'])
        new_block = self.new_block(proof, self.hash_block(last_block))
        logger.info(f"New block mined with hash: {self.hash_block(new_block)}")
        return self.hash_block(new_block)

    def hash_block(self, block):
        """
        Creates a SHA-256 hash of a Block.
        """
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains 4 leading zeroes, where p is the previous p'
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    def valid_proof(self, last_proof, proof):
        """
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def verify_chain(self):
        """
        Verify the integrity of the entire blockchain.
        """
        if not self.chain:
            return True # An empty chain is valid

        current_block = self.chain[0]
        block_index = 1

        while block_index < len(self.chain):
            next_block = self.chain[block_index]
            # Check that the hash of the current block is correct
            if next_block['previous_hash'] != self.hash_block(current_block):
                return False
            # Check that the Proof of Work is correct
            if not self.valid_proof(current_block['proof'], next_block['proof']):
                return False
            current_block = next_block
            block_index += 1
        return True

class FederatedTrainer:
    def __init__(self):
        logger.info("FederatedTrainer initialized (placeholder).")
    def train_model(self, data):
        # This is a placeholder for a federated learning training process
        logger.info(f"Simulating federated training with {len(data)} data points.")
        return {"status": "training initiated", "data_points": len(data)}

# --- End Placeholder ---

# Initialize Flask app
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# Custom rate limiter implementation
class SimpleRateLimiter:
    def __init__(self, max_requests, time_window):
        self.max_requests = max_requests # Max requests allowed
        self.time_window = time_window   # Time window in seconds (e.g., 3600 for 1 hour)
        self.access_records = {} # Stores {ip_address: [timestamp1, timestamp2, ...]}

    def allow_request(self, ip):
        current_time = datetime.now().timestamp()
        
        # Clean up old records outside the time window
        self.access_records[ip] = [
            t for t in self.access_records.get(ip, [])
            if current_time - t < self.time_window
        ]
        
        # Check if the number of requests exceeds the limit
        if len(self.access_records.get(ip, [])) < self.max_requests:
            self.access_records.setdefault(ip, []).append(current_time)
            return True
        return False

# Initialize modules
predictor = ComplaintPredictor()
ledger = ComplaintLedger()
trainer = FederatedTrainer()
limiter = SimpleRateLimiter(max_requests=100, time_window=3600) # 100 requests per hour per IP

# Security middleware: Apply rate limiting to all requests
@app.before_request
def limit_requests():
    """Apply rate limiting to all requests based on IP address."""
    if not limiter.allow_request(request.remote_addr):
        logger.warning(f"Rate limit exceeded for IP: {request.remote_addr}")
        return jsonify({"error": "Too many requests"}), 429

# Database initialization
def init_db():
    """Initialize database with proper schema."""
    with sqlite3.connect("complaints.db") as conn:
        cursor = conn.cursor()

        # Complaints table schema (updated for technician assignment and location)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                problem TEXT,
                address TEXT,
                complaint_latitude REAL,  -- Latitude of the complaint
                complaint_longitude REAL, -- Longitude of the complaint
                error_code TEXT,
                contact_no TEXT,
                media_path TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending', -- e.g., 'pending', 'assigned', 'resolved'
                assigned_technician_id INTEGER, -- Foreign key to technicians table
                assigned_technician_name TEXT,  -- Redundant but useful for quick lookup
                synced_to_server BOOLEAN DEFAULT 0
            )
        """)

        # Technicians table schema (with availability status and geographical coordinates)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS technicians (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                contact_no TEXT,
                latitude REAL,
                longitude REAL,
                status TEXT, -- 'available' or 'busy'
                specialization TEXT -- e.g., 'AC,Refrigerator,TV'
            )
        """)

        # Insert 100 fixed sample technicians if table is empty
        cursor.execute("SELECT COUNT(*) FROM technicians")
        if cursor.fetchone()[0] == 0:
            logger.info("Technicians table is empty. Populating with 100 fixed sample technicians in Pune region.")
            
            # --- Predefined base locations (approximate for Pune and nearby villages) ---
            # Each tuple: (Location Name, Latitude, Longitude, Num_Technicians_Here)
            base_locations = [
                ("Shivajinagar (Central)", 18.5204, 73.8567, 10),
                ("Pimpri-Chinchwad", 18.6255, 73.8096, 12),
                ("Hadapsar", 18.5137, 73.9310, 10),
                ("Hinjewadi (IT Hub)", 18.5913, 73.7389, 15),
                ("Kothrud", 18.5082, 73.7915, 8),
                ("Deccan Gymkhana", 18.5140, 73.8407, 5),
                ("Aundh", 18.5583, 73.8092, 7),
                ("Kharadi", 18.5670, 73.9400, 8),
                ("Viman Nagar", 18.5630, 73.9180, 5),
                ("Nigdi", 18.6600, 73.7740, 6),
                ("Talegaon Dabhade (Rural)", 18.7300, 73.6600, 4),
                ("Uruli Kanchan (Rural)", 18.4167, 74.0500, 4),
                ("Pirangut (Rural)", 18.4901, 73.6669, 3),
                ("Khed (Rural North)", 18.8687, 73.8755, 3),
                ("Saswad (Rural South)", 18.3060, 74.0320, 2),
                ("Lonavala (Outskirts)", 18.7500, 73.4000, 3) # Even outer areas
            ]
            
            # Fixed small offsets for spreading technicians around a base location
            # These values ensure distinct but consistently close points for each technician
            offsets = [
                (0.001, 0.002), (-0.002, 0.001), (0.003, -0.001), (-0.001, -0.003),
                (0.002, 0.003), (-0.003, 0.002), (0.0015, -0.0025), (-0.0025, 0.0015),
                (0.004, 0.0005), (-0.0005, -0.004), (0.000, 0.001), (0.001, 0.000),
                (0.002, -0.0005), (-0.0005, 0.002), (0.001, 0.001), (-0.001, -0.001),
                (0.003, 0.003), (-0.003, -0.003), (0.001, 0.0005), (-0.0005, 0.001),
                (0.0005, -0.001), (-0.001, 0.0005), (0.0025, 0.001), (-0.001, 0.0025),
                (0.0008, 0.0012), (-0.0012, 0.0008), (0.0018, -0.0008), (-0.0008, -0.0018),
                (0.0022, 0.0028), (-0.0028, 0.0022), (0.0011, -0.0021), (-0.0021, 0.0011)
            ] * 3 # Repeat offsets to ensure enough unique pairs for all technicians
            
            specializations_pool = [
                "AC", "Refrigerator", "Washing Machine", "TV", "Geyser",
                "Microwave", "Induction", "Dishwasher", "Water Purifier"
            ]
            
            first_names = ["Rahul", "Priya", "Amit", "Sneha", "Vikas", "Pooja", "Sanjay", "Meena", 
                           "Arjun", "Kavita", "Ravi", "Nisha", "Ashok", "Sita", "Gaurav", "Divya", 
                           "Kapil", "Preeti", "Manoj", "Anjali", "Dinesh", "Kiran", "Vivek", "Shilpa",
                           "Rohit", "Ritu", "Mohan", "Sapna", "Ajay", "Swati"]
            last_names = ["Kumar", "Patil", "Joshi", "Singh", "Sharma", "Reddy", "Yadav", "Gupta", 
                          "Malik", "Verma", "Khan", "Desai", "Rao", "Naidu", "Chauhan", "Mehta", 
                          "Dubey", "Pandey", "Saxena", "Bansal", "Chavan", "Kulkarni", "Bhagat", "Sutar",
                          "More", "Kale", "Gaikwad", "Shinde", "Jadhav", "Pawar"]
            
            technicians_data = []
            tech_counter = 0

            for base_name, base_lat, base_lon, num_techs in base_locations:
                for i in range(num_techs):
                    if tech_counter >= 100: # Ensure we don't exceed 100 technicians
                        break

                    # Use fixed offsets based on counter for deterministic "spread"
                    offset_lat, offset_lon = offsets[tech_counter % len(offsets)]
                    
                    tech_lat = round(base_lat + offset_lat, 6)
                    tech_lon = round(base_lon + offset_lon, 6)

                    # Generate fixed names (deterministic based on counter)
                    name = f"{first_names[tech_counter % len(first_names)]} {last_names[tech_counter % len(last_names)]}"
                    
                    # Generate fixed 10-digit contact numbers (deterministic based on counter)
                    contact_num_suffix = str(tech_counter + 1000000000)[-9:] # ensure 9 digits
                    contact_no = f"9{contact_num_suffix}" 

                    status = 'available' if tech_counter % 2 == 0 else 'busy' # Alternate available/busy
                    
                    # Fixed specializations (deterministic based on counter)
                    # Pick 1 to 3 specializations
                    num_specs_for_tech = (tech_counter % 3) + 1 
                    tech_specializations_indices = sorted([(tech_counter + j) % len(specializations_pool) for j in range(num_specs_for_tech)])
                    specialization = ",".join([specializations_pool[idx] for idx in tech_specializations_indices])
                    
                    technicians_data.append((name, contact_no, tech_lat, tech_lon, status, specialization))
                    tech_counter += 1
                if tech_counter >= 100:
                    break

            cursor.executemany("""
                INSERT INTO technicians (name, contact_no, latitude, longitude, status, specialization)
                VALUES (?, ?, ?, ?, ?, ?)
            """, technicians_data)
            logger.info(f"Inserted {len(technicians_data)} fixed sample technicians.")

        conn.commit()
    logger.info("Database initialized/checked.")

# Call DB initialization on app startup
init_db()

# --- Haversine Distance Calculation ---
def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the distance between two points on Earth using the Haversine formula.
    Returns distance in kilometers.
    """
    R = 6371  # Radius of Earth in kilometers

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance # Distance in kilometers

# --- Technician Assignment Logic ---
def assign_technician(complaint_lat: float, complaint_lon: float, problem: str, error_code: str) -> dict:
    """
    Assigns the most suitable available technician based on proximity and specialization.
    """
    logger.info(f"Attempting to assign technician for problem: '{problem}', error: '{error_code}', location: ({complaint_lat}, {complaint_lon})")
    
    assigned_tech = None
    
    with sqlite3.connect("complaints.db") as conn:
        conn.row_factory = sqlite3.Row # Allows accessing columns by name
        cursor = conn.cursor()
        
        # Fetch all available technicians with their specializations and locations
        cursor.execute("""
            SELECT id, name, contact_no, latitude, longitude, specialization
            FROM technicians 
            WHERE status = 'available'
        """)
        available_technicians = cursor.fetchall()
        
        if not available_technicians:
            logger.warning("No available technicians found for assignment.")
            return {"status": "no_available_technician", "details": "No technicians are currently available."}

        # Determine required specializations based on problem/error code
        required_specs = set()
        problem_lower = problem.lower()
        error_code_upper = error_code.upper()

        # Simple keyword-based mapping for specialization
        if "ac" in problem_lower or "cooling" in problem_lower or "e1" in error_code_upper or "h1" in error_code_upper:
            required_specs.add("AC")
        if "refrigerator" in problem_lower or "fridge" in problem_lower or "f0" in error_code_upper:
            required_specs.add("Refrigerator")
        if "washing machine" in problem_lower or "wash" in problem_lower:
            required_specs.add("Washing Machine")
        if "tv" in problem_lower or "display" in problem_lower:
            required_specs.add("TV")
        if "induction" in problem_lower:
            required_specs.add("Induction")
        if "microoven" in problem_lower or "microwave" in problem_lower:
            required_specs.add("Microwave")
        if "geyser" in problem_lower:
            required_specs.add("Geyser")
        if "dishwasher" in problem_lower:
            required_specs.add("Dishwasher")
        if "water purifier" in problem_lower:
            required_specs.add("Water Purifier")
            
        # If no specific specialization is derived, consider technicians with any of the common skills
        if not required_specs:
            logger.info("No specific specialization derived, considering technicians with any specialization.")
            # This 'specializations_pool' comes from the init_db function's scope,
            # so it needs to be accessible here, or redefine it globally/pass it.
            # For simplicity, assuming it's available or re-defining a common list.
            common_specializations = ["AC", "Refrigerator", "Washing Machine", "TV", "Geyser",
                                      "Microwave", "Induction", "Dishwasher", "Water Purifier"]
            required_specs = set(common_specializations) 
            if not required_specs: 
                required_specs.add("General Appliance") # Fallback for extremely broad cases

        # Filter and sort technicians
        candidate_technicians = []
        for tech in available_technicians:
            # Convert technician's specializations to a set of uppercase strings for easy checking
            tech_specs = {s.strip().upper() for s in tech['specialization'].split(',')}
            
            # Check if technician has at least one required specialization
            has_required_spec = any(req_s.upper() in tech_specs for req_s in required_specs)
            
            if has_required_spec:
                # Calculate distance only if complaint coordinates are valid (not None)
                if complaint_lat is not None and complaint_lon is not None and tech['latitude'] is not None and tech['longitude'] is not None:
                    distance = haversine_distance(
                        complaint_lat, complaint_lon,
                        tech['latitude'], tech['longitude']
                    )
                    candidate_technicians.append((distance, tech))
                else:
                    # If no complaint coordinates, assign infinite distance.
                    # These technicians will be considered after any proximity-matched ones,
                    # effectively falling back to specialization/random order if no coordinates are provided.
                    candidate_technicians.append((float('inf'), tech)) 

        # Sort candidates: closest first. If distances are equal (e.g., all inf), their relative order is stable.
        candidate_technicians.sort(key=lambda x: x[0])

        if candidate_technicians:
            assigned_tech_row = candidate_technicians[0][1] # Get the top candidate (closest/first available)
            assigned_tech = dict(assigned_tech_row) # Convert to dictionary for easy access

            # Update technician status to 'busy' in the database
            cursor.execute("""
                UPDATE technicians
                SET status = 'busy'
                WHERE id = ?
            """, (assigned_tech['id'],))
            conn.commit()
            logger.info(f"Assigned technician: {assigned_tech['name']} (ID: {assigned_tech['id']})")
            return {"status": "assigned", "technician": assigned_tech}
        else:
            logger.warning("No suitable technician found matching criteria (available and specialized).")
            return {"status": "no_suitable_technician", "details": "No available technician matches your problem's requirements."}


@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    """
    Handles new complaint submissions from the Telegram bot.
    Receives JSON data, saves to SQLite, adds to blockchain, and assigns a technician.
    """
    try:
        data = request.get_json()
        if not data:
            logger.warning("No JSON data received for complaint submission.")
            return jsonify({"error": "No JSON data received"}), 400

        logger.info(f"Received complaint data: {data}")

        # Validate required fields and their types
        required_fields = {
            'chat_id': int,
            'problem': str,
            'address': str,
            'contact_no': str,
            'error_code': str # error_code can be "NOT_PROVIDED" or actual code
        }
        
        for field, field_type in required_fields.items():
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return jsonify({"error": f"Missing required field: {field}"}), 400
            # Attempt type conversion to ensure correct type, handle potential errors
            try:
                if field_type == int:
                    data[field] = int(data[field])
                elif field_type == str:
                    data[field] = str(data[field])
            except (ValueError, TypeError):
                logger.error(f"Invalid type for field '{field}'. Expected {field_type}, got {type(data[field])} or unconvertible value.")
                return jsonify({"error": f"Invalid data for '{field}'. Expected {field_type}"}), 400

        # Extract optional fields, ensuring correct types or None
        media_path = data.get('media_path', '')
        
        # Convert latitude/longitude to float, handling None or invalid input gracefully
        complaint_latitude = data.get('complaint_latitude')
        complaint_longitude = data.get('complaint_longitude')
        
        if complaint_latitude is not None:
            try: complaint_latitude = float(complaint_latitude)
            except (ValueError, TypeError): complaint_latitude = None # Set to None if conversion fails
            
        if complaint_longitude is not None:
            try: complaint_longitude = float(complaint_longitude)
            except (ValueError, TypeError): complaint_longitude = None # Set to None if conversion fails

        error_code = str(data.get('error_code', 'UNKNOWN')).strip().upper()

        assigned_tech_id = None
        assigned_tech_name = None
        assigned_tech_details = {}
        initial_status = 'pending_assignment' # Default status if no tech is assigned

        # Attempt to assign technician based on location (if provided) and specialization
        assignment_result = assign_technician(
            complaint_latitude, complaint_longitude,
            data['problem'], error_code
        )
        
        if assignment_result['status'] == 'assigned':
            assigned_tech_details = assignment_result['technician']
            assigned_tech_id = assigned_tech_details['id']
            assigned_tech_name = assigned_tech_details['name']
            initial_status = 'assigned' # Update status if assignment successful
            logger.info(f"Complaint successfully assigned to technician: {assigned_tech_name}")
        else:
            logger.warning(f"Technician assignment failed: {assignment_result['details']}")
            assigned_tech_details = {"message": assignment_result['details']} # Provide reason for failure

        # Connect to SQLite database and insert complaint data
        with sqlite3.connect("complaints.db") as conn:
            conn.row_factory = sqlite3.Row # Allows accessing columns by name (e.g., row['column_name'])
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO complaints 
                    (chat_id, problem, address, complaint_latitude, complaint_longitude, 
                     error_code, contact_no, media_path, synced_to_server, 
                     assigned_technician_id, assigned_technician_name, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data['chat_id'],
                    data['problem'],
                    data['address'],
                    complaint_latitude,
                    complaint_longitude,
                    error_code,
                    data['contact_no'],
                    media_path,
                    1, # Mark as synced to server
                    assigned_tech_id,
                    assigned_tech_name,
                    initial_status 
                ))
                
                complaint_id = cursor.lastrowid # Get the ID of the newly inserted row
                conn.commit() # Commit changes to the database

                logger.info(f"Complaint {complaint_id} saved to SQLite database.")

                # Retrieve the full complaint record for blockchain
                cursor.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,))
                complaint = dict(cursor.fetchone()) # Convert Row object to dictionary
                
                # Prepare data for blockchain record
                complaint_record = {
                    'db_id': complaint_id,
                    'user_id': data['chat_id'],
                    'problem': data['problem'],
                    'location_address': data['address'],
                    'location_coords': {'lat': complaint_latitude, 'lon': complaint_longitude} if complaint_latitude is not None else None,
                    'error_code': error_code,
                    'timestamp': datetime.now().isoformat(),
                    'assigned_technician': assigned_tech_name if assigned_tech_name else "N/A"
                }
                
                blockchain_hash = ledger.add_complaint(complaint_record) # Add complaint to blockchain
                logger.info(f"Complaint {complaint_id} added to blockchain. Hash: {blockchain_hash}")
                
                # Return successful response to the bot
                return jsonify({
                    "message": "Complaint registered successfully",
                    "complaint_id": complaint_id,
                    "blockchain_hash": blockchain_hash,
                    "details": complaint, # Include all saved complaint details
                    "assigned_technician": assigned_tech_details # Include technician details for bot to display
                }), 200
                
            except sqlite3.Error as e:
                conn.rollback() # Rollback changes if a database error occurs
                logger.error(f"Database error during complaint submission: {e}", exc_info=True)
                return jsonify({
                    "error": "Database operation failed",
                    "details": str(e)
                }), 500
                
    except Exception as e:
        logger.error(f"Unexpected error during complaint submission: {e}", exc_info=True)
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/api/blockchain', methods=['GET'])
def get_blockchain():
    """Endpoint to view blockchain data."""
    logger.info("Blockchain data requested.")
    return jsonify({
        "chain": ledger.chain,
        "length": len(ledger.chain),
        "pending_complaints": ledger.current_complaints
    })

@app.route('/api/complaints', methods=['GET'])
def get_complaints():
    """Endpoint to fetch all complaints."""
    logger.info("All complaints requested.")
    with sqlite3.connect("complaints.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM complaints ORDER BY timestamp DESC")
        complaints = [dict(row) for row in cursor.fetchall()] # Convert all rows to dictionaries
        
        return jsonify({
            "complaints": complaints,
            "count": len(complaints)
        })

# NEW: Endpoint to fetch technicians data as JSON for live map updates
@app.route('/api/technicians_live', methods=['GET'])
def get_technicians_live():
    """Endpoint to fetch live technician data for the map."""
    logger.info("Live technician data requested.")
    with sqlite3.connect("complaints.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, contact_no, latitude, longitude, status, specialization FROM technicians")
        technicians = [dict(row) for row in cursor.fetchall()]
        return jsonify({"technicians": technicians})

@app.route('/dashboard')
def dashboard():
    """Renders the main dashboard HTML page."""
    logger.info("Dashboard requested.")
    try:
        with sqlite3.connect("complaints.db") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Fetch recent complaints for the dashboard
            cursor.execute("SELECT * FROM complaints ORDER BY timestamp DESC LIMIT 50")
            complaints = [dict(row) for row in cursor.fetchall()]
            
            # Fetch all technicians for the dashboard (initial load)
            cursor.execute("SELECT * FROM technicians")
            technicians = [dict(row) for row in cursor.fetchall()] # This is now for initial render and table

            return render_template('dashboard.html',
                                   complaints=complaints,
                                   technicians=technicians, # Still pass initial data
                                   blockchain_status=len(ledger.chain),
                                   blockchain_valid=ledger.verify_chain())
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}", exc_info=True)
        return "Error loading dashboard.", 500 # Return a simple error message

@app.route('/api/verify_blockchain', methods=['GET'])
def verify_blockchain():
    """Endpoint to verify the integrity of the blockchain."""
    is_valid = ledger.verify_chain()
    logger.info(f"Blockchain verification status: {is_valid}")
    return jsonify({
        "valid": is_valid,
        "chain_length": len(ledger.chain),
        "last_block_hash": ledger.hash_block(ledger.chain[-1]) if ledger.chain else None
    })

@app.route('/')
def home():
    """Root endpoint that returns basic server info."""
    logger.info("Home endpoint accessed.")
    return jsonify({
        "status": "active",
        "service": "Haier Complaint System Backend",
        "version": "1.0",
        "endpoints": {
            "submit_complaint": "/submit_complaint (POST)",
            "get_complaints": "/api/complaints (GET)",
            "blockchain_data": "/api/blockchain (GET)",
            "verify_blockchain": "/api/verify_blockchain (GET)",
            "dashboard": "/dashboard (GET)",
            "health_check": "/health (GET)"
        }
    })

@app.route('/health')
def health_check():
    """Simple health check endpoint."""
    logger.info("Health check requested.")
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    # Run the Flask app in debug mode (useful for development, turn off for production)
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)
