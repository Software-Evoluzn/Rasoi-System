

const grainGrid = document.getElementById("grainGrid");

// FETCH GRAINS FROM API

fetch('/api/grains')

.then(response => response.json())

.then(grains => {

        grains.forEach(grain => {

            const grainCard = `

            <label class="grain_card">

                <input
                    type="radio"
                    name="grain_select"
                    value="${grain.value_name}"
                >

                <div class="grain_card_content">

                    <img
                        src="${grain.image}"
                        alt="${grain.name}"
                    >

                    <span>${grain.name}</span>

                </div>

            </label>
        `;


            // INSERT BEFORE OTHERS CARD

            grainGrid.insertAdjacentHTML(
                "afterbegin",
                grainCard
            );

        });

})

.catch(error => {

        console.log("Error loading grains:", error);

});



    // START BUTTON CLICK

    document.querySelectorAll(".grain_btn")[1]
.addEventListener("click", () => {

    const selectedGrain = document.querySelector(
    'input[name="grain_select"]:checked'
    );

    if (!selectedGrain) {

        alert("Please select grain");

    return;
    }

    const grainValue = selectedGrain.value;


    // REDIRECT TO SINGLE GRAIN PAGE

    window.location.href =
    `/single_grain_page?grain=${grainValue}`;

});

