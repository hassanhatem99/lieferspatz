function weiter() {
  window.location.href = "file:///C:/Users/alysw/OneDrive/Desktop/Lieferpatz/edit%20page/index.html";
}
function handleFile() {
    const input = document.getElementById('photoInput');
    const file = input.files[0];

  }

  function Upload() {
    const input = document.getElementById('photoInput');
    const file = input.files[0];

    if (file) {

      alert('File submitted! You can handle the file data on the server side.');
    } else {
      alert('Please choose an image before submitting.');
    }
  }
