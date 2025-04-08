document.getElementById('clinic-search-form').addEventListener('submit', function(event) {
  event.preventDefault();
  const suburb = document.getElementById('suburb').value;
 

  console.log(`Searching for suburb: ${suburb}`); // Add logging
 

  // Execute the command and capture the output
  fetch('/execute_command', {
  method: 'POST',
  headers: {
  'Content-Type': 'application/json'
  },
  body: JSON.stringify({ command: "", suburb: suburb }) // Send suburb to the server
  })
  .then(response => {
  console.log(`Response received: ${response.status}`); // Add logging
  return response.json();
  })
  .then(data => {
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = ''; // Clear previous results
 

  if (suburb === 'omayzi') {
  // Display scraped data
  resultsDiv.innerHTML = `<pre>${data.data}</pre>`;
  console.log(`Scraped data: ${data.data}`); // Add logging
  } else if (data.clinics && data.clinics.length > 0) {
  // Create table
  const table = document.createElement('table');
  table.innerHTML = `
  <thead>
  <tr>
  <th>Name</th>
  <th>Address</th>
  <th>Phone</th>
  <th>Rating</th>
  </tr>
  </thead>
  <tbody>
  </tbody>
  `;
  resultsDiv.appendChild(table);
  const tbody = table.querySelector('tbody');
 

  data.clinics.forEach(clinic => {
  const row = document.createElement('tr');
  row.innerHTML = `
  <td>${clinic.name || 'N/A'}</td>
  <td>${clinic.address || 'N/A'}</td>
  <td>${clinic.phone || 'N/A'}</td>
  <td>${clinic.rating || 'N/A'}</td>
  `;
  tbody.appendChild(row);
  });
  } else {
  resultsDiv.innerHTML = '<p>No clinics found.</p>';
  }
  })
  .catch(error => {
  console.error('Error:', error);
  resultsDiv.innerHTML = '<p>An error occurred.</p>';
  });
  });