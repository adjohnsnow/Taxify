document.addEventListener("DOMContentLoaded", function () {
  const uploadInput = document.getElementById("file");
  const uploadLabel = document.getElementById("upload-label");

  uploadInput.addEventListener("change", function () {
    const fileName = this.files[0].name;
    uploadLabel.textContent = `Uploaded: ${fileName}`;
  });

  const submitButton = document.getElementById("center-button");
  submitButton.addEventListener("click", function (event) {
    console.log("Button clicked!"); // Check if the button click is registered in the console
    submitForm(event);
  });

  function submitForm(event) {
    console.log("Submitting form..."); // Check if the function is called

    const formData = new FormData(document.getElementById("upload-form"));

    // Replace '/extract_data' with the correct server endpoint URL
    fetch('/extract_data', {
      method: 'POST',
      body: formData,
    })
      .then(response => response.json())
      .then(data => {
        // Handle the response from the server
        console.log(data);

        // Update the tax-amount element with the received tax amount
        const taxAmountElement = document.querySelector('.tax-amount');
        taxAmountElement.textContent = `Rs. ${data.taxAmount.toFixed(2)}`; // Assuming taxAmount is a number

        // You can perform any other actions based on the server response
      })
      .catch(error => {
        console.error('Error:', error);
      })
      .finally(() => {
        // Re-enable the form after processing
        document.getElementById("upload-form").reset();
      });

    event.preventDefault(); // Prevent the default form submission behavior
  }
});
