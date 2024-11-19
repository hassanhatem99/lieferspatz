
function orders() {
  window.location.href = "file:///C:/Users/alysw/OneDrive/Desktop/lieferpatz/R.O%20History/index.html";
}

var activeContainerId = null;

function toggleContentEditable(containerId) {
  var container = document.querySelector('[data-container-id="' + containerId + '"]');

  if (!container) {
    console.error('Container not found:', containerId);
    return;
  }

  if (activeContainerId && activeContainerId !== containerId) {
    disableContentEditable(activeContainerId);
  }

  var elements = container.querySelectorAll('.editable-element');

  elements.forEach(function (element) {
    if (element.tagName !== 'BUTTON') {
      element.toggleAttribute('contenteditable');
    }
  });

  container.classList.toggle('bordered');

  if (container.classList.contains('bordered')) {
    activeContainerId = containerId;
  } else {
    activeContainerId = null;
  }
}

// Function to remove the container
function removeContainer(containerId) {
  var container = document.querySelector('[data-container-id="' + containerId + '"]');

  if (container) {
      container.parentNode.removeChild(container);
  } else {
      console.error('Container not found:', containerId);
  }
}

// Event delegation to handle button clicks on any container
document.body.addEventListener('click', function(event) {
  var targetButton = event.target;

  if (targetButton.tagName === 'BUTTON') {
      var containerId = targetButton.getAttribute('data-container-id');

      if (targetButton.id === 'toggleButton') {
          toggleContentEditable(containerId);
      } else if (targetButton.id === 'removeButton') {
          removeContainer(containerId);
      }
  }
});
// Function to clone the template and append it to the container
function addItem() {
  var productsContainer = document.getElementById('products');
  var template = document.querySelector('.item-template');

  // Clone the template
  var newItem = template.cloneNode(true);

  // Generate a unique container ID
  var containerId = 'rectangle-' + (productsContainer.children.length + 1);

  // Set the data-container-id attribute in the cloned item
  newItem.setAttribute('data-container-id', containerId);

  // Set data-container-id for buttons inside the cloned item
  var buttons = newItem.querySelectorAll('[data-container-id=""]');
  buttons.forEach(function(button) {
    button.setAttribute('data-container-id', containerId);
  });

  // Display the cloned item by removing the "display: none" style
  newItem.style.display = '';

  // Append the new item to the container
  productsContainer.appendChild(newItem);
}

var translateX = 0;
var widthEl = $('.button-groub-Medicine').width();
$('.btn-left').click(function(e) {
    e.preventDefault();
  if(translateX < 0 ) {
     translateX = 0;
  }
  if (translateX >= 0 && translateX <= 120) {
    translateX += 10;
    // $('.button-groub-Medicine').toggleClass("mostafasss");
    $('.button-groub-Medicine').css('transform', 'translateX( -' + translateX + '%)');
            
  }   
});

$('.btn-right').click(function(e) {
    e.preventDefault();
  if(translateX >= 120 ) {
     translateX = 120;
  }
  if (translateX >= 0 && translateX <= 120) {
     translateX -= 10;
    // $('.button-groub-Medicine').toggleClass("mostafasss");
    $('.button-groub-Medicine').css('transform', 'translateX( -' + translateX + '%)');
           
  }   
});




