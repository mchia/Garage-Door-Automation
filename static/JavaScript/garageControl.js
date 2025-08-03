export default function sendCommand(commandId) {
    fetch(`/${commandId}`, {
        method: 'GET'
    })
    .then(response => {
        if (response.ok) {
            console.log(`${commandId} command sent successfully.`);
        } else {
            console.error(`${commandId} failed.`);
        }
    })
    .catch(error => console.error('Error:', error));
}