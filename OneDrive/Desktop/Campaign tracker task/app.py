from flask import Flask, request, jsonify, render_template_string
import json
import os

app = Flask(__name__)
DATA_FILE = 'campaigns.json'

# HTML, CSS, JS as one string (UI: form, search, table, sort)
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Campaign Tracker</title>
<style>
body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background:#eef2f7; color:#333; margin:0; padding:20px;}
h1 { text-align:center; color:#2c3e50; margin-bottom:30px;}
form { max-width:700px; margin:0 auto 20px; display:flex; flex-wrap:wrap; gap:10px; background:#fff; padding:25px; border-radius:12px; box-shadow:0 6px 12px rgba(0,0,0,0.1);}
input, select, button { padding:12px; font-size:16px; border:1px solid #ccc; border-radius:6px;}
input, select { flex:1 1 45%; }
button { background:#4a90e2; color:white; border:none; cursor:pointer; flex:1 1 100%; margin-top:10px; transition:0.3s;}
button:hover { background:#357ab8; }

#search { max-width:700px; margin:15px auto; display:block; padding:10px; border-radius:6px; border:1px solid #ccc; }

table { width:90%; margin:20px auto; border-collapse:collapse; background:#fff; border-radius:10px; overflow:hidden; box-shadow:0 6px 12px rgba(0,0,0,0.1);}
th, td { padding:14px 16px; text-align:center;}
th { background:#4a90e2; color:#fff; cursor:pointer;}
tr:nth-child(even){background:#f5f7fa;}
tr:hover{background:#d0e4fc;}
.action-btn{margin:2px; padding:6px 10px; font-size:14px; border-radius:5px; border:none; cursor:pointer;}
.active-btn{background:#27ae60;color:white;}
.paused-btn{background:#f39c12;color:white;}
.completed-btn{background:#8e44ad;color:white;}
.delete-btn{background:#c0392b;color:white;}
</style>
</head>
<body>

<h1>Campaign Tracker</h1>

<form id="campaignForm">
<input type="text" id="name" placeholder="Campaign Name" required>
<input type="text" id="client" placeholder="Client Name" required>
<input type="date" id="startDate" required>
<select id="status">
<option>Active</option>
<option>Paused</option>
<option>Completed</option>
</select>
<button type="submit">Add Campaign</button>
</form>

<!-- Search -->
<input type="text" id="search" placeholder="Search campaigns by name/client...">

<table id="campaignTable">
<tr>
<th>Name</th>
<th>Client</th>
<th onclick="sortTable(2)">Start Date ⬍</th>
<th>Status</th>
<th>Actions</th>
</tr>
</table>

<script>
const API = '/campaigns';

async function fetchCampaigns() {
    const res = await fetch(API);
    const data = await res.json();

    const table = document.getElementById('campaignTable');
    table.innerHTML = `<tr>
<th>Name</th>
<th>Client</th>
<th onclick="sortTable(2)">Start Date ⬍</th>
<th>Status</th>
<th>Actions</th>
</tr>`;
    data.forEach(c=>{
        const row = table.insertRow();
        row.insertCell(0).innerText = c.name;
        row.insertCell(1).innerText = c.client;
        row.insertCell(2).innerText = c.startDate;
        row.insertCell(3).innerText = c.status;
        row.cells[3].style.color = c.status==='Active'?'green':c.status==='Paused'?'orange':'purple';
        row.insertCell(4).innerHTML = `
<button class="action-btn active-btn" onclick="updateStatus('${c.name}','Active')">Active</button>
<button class="action-btn paused-btn" onclick="updateStatus('${c.name}','Paused')">Paused</button>
<button class="action-btn completed-btn" onclick="updateStatus('${c.name}','Completed')">Completed</button>
<button class="action-btn delete-btn" onclick="deleteCampaign('${c.name}')">Delete</button>`;
    });
}

// Add Campaign
async function addCampaign(event){
    event.preventDefault();
    const name = document.getElementById('name').value.trim();
    const client = document.getElementById('client').value.trim();
    const startDate = document.getElementById('startDate').value;
    const status = document.getElementById('status').value;
    if(!name || !client || !startDate){ alert('Please fill all fields'); return; }
    await fetch(API,{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({name,client,startDate,status})
    });
    document.getElementById('campaignForm').reset();
    fetchCampaigns();
}

// Update Status
async function updateStatus(name,status){
    await fetch(`${API}/${encodeURIComponent(name)}`,{
        method:'PUT',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({status})
    });
    fetchCampaigns();
}

// Delete Campaign
async function deleteCampaign(name){
    if(confirm(`Are you sure you want to delete "${name}"?`)){
        await fetch(`${API}/${encodeURIComponent(name)}`,{method:'DELETE'});
        fetchCampaigns();
    }
}

// Search
document.getElementById('search').addEventListener('input',function(){
    const query = this.value.toLowerCase();
    const rows = document.querySelectorAll('#campaignTable tr:not(:first-child)');
    rows.forEach(row=>{
        const name=row.cells[0].innerText.toLowerCase();
        const client=row.cells[1].innerText.toLowerCase();
        row.style.display=(name.includes(query)||client.includes(query))?'':'none';
    });
});

// Sort by Start Date
function sortTable(colIndex){
    const table = document.getElementById("campaignTable");
    let rows = Array.from(table.rows).slice(1);
    let asc = table.getAttribute("data-sort")!=="asc";
    rows.sort((a,b)=>{
        let dateA = new Date(a.cells[colIndex].innerText);
        let dateB = new Date(b.cells[colIndex].innerText);
        return asc?dateA-dateB:dateB-dateA;
    });
    rows.forEach(r=>table.appendChild(r));
    table.setAttribute("data-sort", asc?"asc":"desc");
}

document.getElementById('campaignForm').addEventListener('submit',addCampaign);
fetchCampaigns();
</script>
</body>
</html>
"""

# JSON helper functions
def load_campaigns():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE,'w') as f:
            json.dump([],f)
    with open(DATA_FILE,'r') as f:
        return json.load(f)

def save_campaigns(campaigns):
    with open(DATA_FILE,'w') as f:
        json.dump(campaigns,f,indent=2)

# Flask routes
@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/campaigns',methods=['GET'])
def get_campaigns():
    return jsonify(load_campaigns())

@app.route('/campaigns',methods=['POST'])
def add_campaign():
    campaigns = load_campaigns()
    data = request.json
    # prevent duplicate names (optional)
    campaigns = [c for c in campaigns if c['name'] != data.get('name')]
    campaigns.append(data)
    save_campaigns(campaigns)
    return jsonify({'message':'Campaign added!'})

@app.route('/campaigns/<path:name>',methods=['PUT'])
def update_campaign(name):
    campaigns = load_campaigns()
    decoded_name = name
    for c in campaigns:
        if c['name'] == decoded_name:
            c['status'] = request.json.get('status', c.get('status'))
            save_campaigns(campaigns)
            return jsonify({'message':'Status updated!'})
    return jsonify({'message':'Campaign not found'}),404

@app.route('/campaigns/<path:name>',methods=['DELETE'])
def delete_campaign(name):
    campaigns = load_campaigns()
    decoded_name = name
    campaigns = [c for c in campaigns if c['name'] != decoded_name]
    save_campaigns(campaigns)
    return jsonify({'message':'Campaign deleted!'})

if __name__ == '__main__':
    # Use PORT env var if provided (Render sets $PORT)
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

