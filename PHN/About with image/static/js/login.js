const users = [
    { username: "user", password: "user123", type: "user" },
    { username: "admin", password: "admin123", type: "admin" }
];

document.getElementById('loginForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    const user = users.find(u => u.username === username && u.password === password);
    if (user) {
        if (user.type === "user") {
            window.location.href = '/user_dashboard'; // Redirect to User Dashboard
        } else if (user.type === "admin") {
            window.location.href = '/admin_dashboard'; // Redirect to Admin Dashboard
        }
    } else {
        alert("Invalid credentials!");
    }
});
