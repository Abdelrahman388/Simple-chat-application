document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    fetch('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username, password: password })
    })
    .then(response => {
      if (!response.ok) {
        return response.json().then(data => { throw new Error(data.msg || "Login failed") });
      }
      return response.json();
    })
    .then(data => {
      if (data.access_token) {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('username',username)
        window.location.href = '/chat';
      } else {
        alert("Login failed");
      }
    })
    .catch(error => {
      console.error('Error:', error);
      alert(error.message);
    });
  });