  function togglePass(id, btn) {
            const input = document.getElementById(id);
            const icon = btn.querySelector('i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('ti-eye');
                icon.classList.add('ti-eye-off');
            } else {
                input.type = 'password';
                icon.classList.remove('ti-eye-off');
                icon.classList.add('ti-eye');
            }
        }

document.getElementById("registerBtn").addEventListener("click" , async function () {
    const name  = document.getElementById("name").value;
    const password  = document.getElementById("signupPassword").value;
    const confirmPassword  = document.getElementById("confirmPassword").value;
    const email  = document.getElementById("email").value;
    const mobile  = document.getElementById("mobile").value;
   

    //validations

      if (!name || !password || !confirmPassword || !email || !mobile) {
          alert("Please fill all fields");
          return;
       }

      if (password !== confirmPassword) {
          alert("Passwords do not match");
          return;
      }
     
      try{

         const response = await fetch("http://192.168.1.53:5000/register", {

              method: "POST",
               headers: {
                "Content-Type": "application/json"
            },
              body: JSON.stringify({
                name: name,
                mobile: mobile,
                email: email,
                password:password
               
            })

         });

          const data = await response.json();

            if (response.ok) {

            alert(data.message);

            // Redirect to login page
            window.location.href = "/";

        } else {

            alert(data.error);

        }


      }catch(error){
            console.log(error);
           alert("Server Error");
      }




    
})