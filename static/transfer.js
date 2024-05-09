$('.dropdown1').empty();
$('.dropdown2').empty();

var fromAccount;
function fromOption() {
    var dropdown = document.getElementById("dropdown");
    fromAccount = dropdown.value;

    

    if (fromAccount) {
        
        var dropdown2 = document.getElementById("dropdown2");
        
        for(var i = 0; i < dropdown2.options.length; i++) {
            if (dropdown2.options[i].value == fromAccount) {
                dropdown2.remove(i);
            }
        }
        
        document.getElementById("dropdown2div").style.visibility = "visible";
    }
};

var toAccount;
function toOption() {
    var dropdown = document.getElementById("dropdown2");
    toAccount = dropdown.value;

    document.getElementById("amount").style.visibility = "visible";
}
