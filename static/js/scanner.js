let scanDeviceId = "";

// CREATE QR SCANNER
const html5QrCode = new Html5Qrcode("reader");


// SUCCESS CALLBACK
function onScanSuccess(decodedText) {

    // scanDeviceId = decodedText.split("/").pop();
         scanDeviceId = decodedText.trim();

        alert(
        "Scanned Device ID: " +
        scanDeviceId
    );

    console.log(
        "Scanner Device Id:",
        decodedText
    );

    // STOP CAMERA AFTER SCAN
    html5QrCode.stop();

    // FETCH PRODUCT DETAILS
    fetch(
        `http://192.168.1.53:5000/product/${scanDeviceId}`
    )

    .then(response => response.json())

    .then(data => {

        console.log(data);

        // if (data.error) {

        //     alert(data.error);
        //     return;
        // }

        // SHOW PRODUCT DETAILS
        document.getElementById(
            "serial_number"
        ).innerText =
            data.serial_number;

        document.getElementById(
            "model_name"
        ).innerText =
            data.model_number;

        document.getElementById(
            "mac_id"
        ).innerText =
            data.mac_id;

    })

    .catch(error => {

        console.log(error);

        alert("Server Error");

    });

}


// OPEN CAMERA
document.querySelector(".scanner_open_btn")
.addEventListener("click", async function () {

    try {

        await html5QrCode.start(

            // FORCE BACK CAMERA
            {
                facingMode: "environment"
            },

            {
                fps: 10,

                qrbox: {
                    width: 250,
                    height: 250
                }
            },

            onScanSuccess
        );

    }

    catch (err) {

        console.log(err);

        alert(err);

    }

});


// LINK PRODUCT
document.querySelector(".scanner_link_btn")
.addEventListener("click", async function () {

    const purchase_date =
        document.getElementById(
            "scanner_purchase_date"
        ).value;

    if (!scanDeviceId) {

        alert("Please scan product first");
        return;
    }

    if (!purchase_date) {

        alert("Please select purchase date");
        return;
    }

    try {

        const response = await fetch(

            "http://192.168.1.53:5000/register-product",

            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    device_id: scanDeviceId,

                    
                    purchase_date: purchase_date

                })
            }
        );

        const data = await response.json();

        console.log(data);

        if (response.ok) {

            alert(
                "Product Linked Successfully"
            );

        } else {

            alert(data.error);

        }

    }

    catch (error) {

        console.log(error);

        alert("Server Error");

    }

});