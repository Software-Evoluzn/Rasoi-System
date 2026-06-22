const slider = document.getElementById('textureSlider');
const display = document.getElementById('levelValue');
const decBtn = document.getElementById('decrementBtn');
const incBtn = document.getElementById('incrementBtn');

// Updates filled portion tracking background gradient natively
function updateSliderColor() {
    const min = slider.min || 1;
    const max = slider.max || 20;
    const val = slider.value;
    const percentage = ((val - min) / (max - min)) * 100;

    slider.style.background = `linear-gradient(to right, #794AFC 0%, #794AFC ${percentage}%, #f1f1f1 ${percentage}%, #f1f1f1 100%)`;
}

function handleUpdate() {
    display.textContent = slider.value;
    updateSliderColor();
}

slider.addEventListener('input', handleUpdate);

decBtn.addEventListener('click', () => {
    if (Number(slider.value) > Number(slider.min)) {
        slider.value = Number(slider.value) - 1;
        handleUpdate();
    }
});

incBtn.addEventListener('click', () => {
    if (Number(slider.value) < Number(slider.max)) {
        slider.value = Number(slider.value) + 1;
        handleUpdate();
    }
});

// Run initial configuration setup
updateSliderColor();




// GET GRAIN FROM URL

const params = new URLSearchParams(window.location.search);

const selectedGrain = params.get("grain");


// FETCH ALL GRAINS

fetch('/api/grains')

    .then(response => response.json())

    .then(grains => {

        // FIND SELECTED GRAIN

        const grain = grains.find(item =>
            item.value_name === selectedGrain
        );


        // IF GRAIN FOUND

        if (grain) {

            document.getElementById("grainName")
                .innerText = grain.name;

            document.getElementById("grainImage")
                .src = grain.image;

        }

        // IF OTHERS SELECTED

        else if (selectedGrain === "others") {

            document.getElementById("grainName")
                .innerText = "OTHERS";

            document.getElementById("grainImage")
                .src = "../static/img/others.png";

        }

    })

    .catch(error => {

        console.log("Error loading grain:", error);

    });

