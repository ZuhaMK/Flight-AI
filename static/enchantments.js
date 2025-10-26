async function sendMessage() {
    const input = document.getElementById("chat-input");
    const message = input.value;
    input.value = "";
    if (message !== "") {


        const chatbox = document.getElementById("chat-log");
        chatbox.innerHTML += `<p><strong>You:</strong>${message} </p>`;

        const response = await fetch("/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message})
        });
        const data = await response.json();
        chatbox.innerHTML += `<p><strong>AI:</strong> ${data.reply}</p>`;
    }
}

// Find the element by its ID
let search = ["1","2","3","4","5","6"];

let something = {"minecraft":work}
fetch('/data')
    .then(response => response.json())
    .then(data => {
        document.getElementById('name').textContent = data.name;
        document.getElementById('details').textContent =
            `${data.name} is ${data.age} years old and lives in ${data.city}.`;
    })
    .catch(error => console.error('Error:', error));

for (let i = 0; i < search.length; i++) {

    element = document.getElementById(search[i] + ".1");
    element.innerText = "Hello, JavaScript!";
    element = document.getElementById(search[i] + ".2");
    element.innerText = "· LHR → CDG · 08:35–10:55";
    element = document.getElementById(search[i] + ".3");
    element.innerText = "Please work";
}