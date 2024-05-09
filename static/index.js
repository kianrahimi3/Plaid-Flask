
var public = undefined;
var link_session_id = undefined;
var isSignedIn = false;


(async function($) {
  const link_token = (await $.post('/create_link_token')).link_token;

  var handler = await Plaid.create({
    // Create a new link_token to initialize Link
    token: link_token,
    onLoad: function() {
      // Optional, called when Link loads
    },
    onSuccess: function(public_token, metadata) {
      // Send the public_token to your app server.
      // The metadata object contains info about the institution the
      // user selected and the account ID or IDs, if the
      // Account Select view is enabled.
      public = public_token;
      $.post('/exchange_public_token', {
        public_token: public_token,
      }
    );
    
    var element = document.getElementById("hide");
    element.removeAttribute("hidden");
    },
    onExit: function(err, metadata) {
      // The user exited the Link flow.
      if (err != null) {
        // The user encountered a Plaid API error prior to exiting.
      }
      // metadata contains information about the institution
      // that the user selected and the most recent API request IDs.
      // Storing this information can be helpful for support.
    },
    onEvent: function(eventName, metadata) {
      // Optionally capture Link flow events, streamed through
      // this callback as your users connect an Item to Plaid.
      // For example:
      // eventName = "TRANSITION_VIEW"
      // metadata  = {
      //   link_session_id: "123-abc",
      //   mfa_type:        "questions",
      //   timestamp:       "2017-09-14T14:42:19.350Z",
      //   view_name:       "MFA",
      // }

      link_session_id = metadata["link_session_id"];
    }
  });

  $('#link-button').on('click', function(e) {
    handler.open();
  });

  let element = document.getElementById("hide");
  let hidden = element.getAttribute("hidden");

  if (hidden) {
    element.removeAttribute("hidden");
  }
  

  /*
  $("#get-accounts").on("click", function(event) {
    var temp = $.get('/accounts');
    console.log(temp);
  })
  */
 
  /*
  var test = document.getElementById("test");
    test.addEventListener("click", () => {
    document.getElementById("testSpan").innerHTML = public;
});
*/

})(jQuery);




