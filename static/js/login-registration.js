const form = document.getElementById("registrationForm");
const addPetBtn = document.getElementById("addPetBtn");
const submitBtn = document.getElementById("submitBtn");
const petFields = document.getElementById("petFields");
const successPage = document.getElementById("successPage");
const dogWalkerCheckbox = document.getElementById("dogWalkerCheckbox");

// Counter for tracking the number of added dogs
let petCounter = 0;
let isDogWalker = false;

// Function to add input fields for a dog
function addPetFields() {
  petCounter++;
  const petFieldDiv = document.createElement("div");
  petFieldDiv.innerHTML = `
    <h4>Dog ${petCounter}</h4>
    <div class="form-group">
      <label for="petName${petCounter}">Dog Name</label>
      <input type="text" class="form-control" id="petName${petCounter}" placeholder="Name" />
    </div>
    <div class="form-group">
      <label for="petAge${petCounter}">Dog Age</label>
      <input type="number" class="form-control" id="petAge${petCounter}" placeholder="Age" />
    </div>
    <div class="form-group">
      <label for="petBreed${petCounter}">Dog Breed</label>
      <input type="text" class="form-control" id="petBreed${petCounter}" placeholder="Breed" />
    </div>
  `;
  petFields.appendChild(petFieldDiv);
}

// Add dog fields when the "Add Dog" button is clicked
addPetBtn.addEventListener("click", () => {
  if (!isDogWalker) {
    addPetFields();
  }
});

// Function to disable "Add Dog" button and collapse dog input fields
function disableAddPet() {
  isDogWalker = true;
  addPetBtn.disabled = true;
  petFields.style.display = "none";
}

// Function to enable "Add Dog" button and show dog input fields
function enableAddPet() {
  isDogWalker = false;
  addPetBtn.disabled = false;
  petFields.style.display = "block";
}

// Check the checkbox state when the page loads
if (dogWalkerCheckbox.checked) {
  disableAddPet();
}

// Add an event listener to check the checkbox state
dogWalkerCheckbox.addEventListener("change", function () {
  if (this.checked) {
    disableAddPet();
  } else {
    enableAddPet();
  }
});

async function submitForm() {
  try {
    const email = document.getElementById("exampleInputEmail1").value;
    const password = document.getElementById("exampleInputPassword1").value;
    const checkUserExistsEndpoint = `/check_user_exists?email=${encodeURIComponent(email)}`;
    const isDogWalker = dogWalkerCheckbox.checked; // Get the checkbox state here

    if (!email.includes('@')) {
      alert("Please enter a valid email address (missing '@').");
      return;
    }

    if (!email || !password) {
      alert("Please enter both email and password.");
      return;
    }

    // Perform a GET request to check_user_exists
    const response = await fetch(checkUserExistsEndpoint, {
      method: "GET",
    });

    // Parse the response as a boolean value
    const isRegistered = await response.json();

    if (!isRegistered && !isDogWalker) {
      // Enforce the requirement for a non-dog walker to have at least one dog
      if (petCounter === 0) {
        alert("Non-dog walkers must add at least one dog.");
        return;
      }
    }

    const petData = [];
    // Add pet data to the user
    if (!isDogWalker) {
      for (let i = 1; i <= petCounter; i++) {
        const breed = document.getElementById(`petBreed${i}`).value;
        const name = document.getElementById(`petName${i}`).value;
        const age = document.getElementById(`petAge${i}`).value;
        if (isNaN(age) || age <= 0) {
          alert("Invalid age. Age must be a positive number.");
          return;
        }
        petData.push({ owner: email, breed, name, age });
      }
    }

    const requestBody = {
      user: { email, password, dog_walker: isDogWalker }, // Include dog_walker in the request
      dogs: petData,
    };

    // Use the `isRegistered` variable to determine the endpoint
    let endpoint; // Declare the variable here

    if (isRegistered) {
      endpoint = "/login";
    } else {
      endpoint = "/register";
    }

    // Perform a POST request to the appropriate endpoint
    const response2 = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    });

    if (response2.status === 401) {
      // Display an alert for an incorrect password
      alert("Incorrect password");
    } else if (response.ok) {
      response2.json() // Parse the JSON response
      .then(function(data) {
        // Extract the access_token from the response data
        const access_token = data.access_token_cookie;
        document.cookie = `access_token_cookie=${access_token}; path=/user`;
        // Access_token can now be used in fetch requests to the '/user' endpoint.
        window.location.href = "/user"
      });
    } else {
      // Handle other error conditions, e.g., display an error message
      alert("Failed to submit the form. Please try again later.");
    }
  } catch (error) {
    // Handle any unexpected errors that may occur during the async operations
    console.error("An error occurred:", error);
    alert("An error occurred. Please try again later.");
  }
}

submitBtn.addEventListener("click", submitForm);
