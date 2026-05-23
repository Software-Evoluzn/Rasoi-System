let scanDeviceId = "";

function onScanSuccess(decodedText) {
    scanDeviceId = decodedText;


    //stop scanner

    html5QrcodeScanner.clear();

    //fetch products details

    fetch("http://127.0.0.1:5000/product/" + decodedText)
        .then(response => response.json())
        .then(data => {

            console.log(data);

            document.getElementById("serial_number").innerText =
                data.serial_number;

            document.getElementById("model_name").innerText =
                data.product_name;

            document.getElementById("mac_id").innerText =
                decodedText;

        })
        .catch(error => {

            console.log(error);

            alert("Invalid Product");

        });

}


let html5QrcodeScanner = new Html5QrcodeScanner(
    "reader",
    {
        fps: 10,
        qrbox: 250
    }
);

//open camera 

document.querySelector(".scanner_open_btn")
      .addEventListener("click" , function(){

        html5QrcodeScanner.render(onScanSuccess)

      })

//LINK PRODUCT

document.querySelector(".scanner_link_btn")
.addEventListener("click" , async function(){

    try{

        
       }
       catch(error){
        console.log(error)
       }

});



