let tg = window.Telegram.WebApp;
let user = tg.initDataUnsafe.user;

document.getElementById("name").innerText = user.first_name;

let progress = 0;
let bar = document.getElementById("bar");
let percent = document.getElementById("percent");
let status = document.getElementById("status");

let interval = setInterval(() => {
  progress += 5;
  bar.style.width = progress + "%";
  percent.innerText = progress + "%";

  if (progress >= 100) {
    clearInterval(interval);
    verify();
  }
}, 150);

function getDevice() {
  return JSON.stringify({
    ua: navigator.userAgent,
    screen: screen.width + "x" + screen.height,
    platform: navigator.platform,
    lang: navigator.language
  });
}

function verify() {
  percent.innerText = "Checking...";

  fetch("/verify", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      user_id: user.id,
      device: getDevice()
    })
  })
  .then(res => res.json())
  .then(res => {

    document.getElementById("scanBox").style.display = "none";
    document.getElementById("resultBox").style.display = "block";

    if (res.status === "success") {
      status.className = "badge success";
      status.innerText = "VERIFIED";

      document.getElementById("icon").innerText = "✅";
      document.getElementById("title").innerText = "Success";
      document.getElementById("desc").innerText = "Device Approved";

    } else if (res.status === "failed") {
      status.className = "badge failed";
      status.innerText = "FAILED";

      document.getElementById("icon").innerText = "❌";
      document.getElementById("title").innerText = "Failed";
      document.getElementById("desc").innerText = "Device Already Used";

    } else {
      status.innerText = "SERVER ERROR ❌";
    }

  })
  .catch(() => {
    status.innerText = "SERVER ERROR ❌";
  });
}

function closeApp() {
  tg.close();
}
