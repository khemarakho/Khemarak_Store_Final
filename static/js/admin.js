const menu = document.getElementById("menu-btn");
const sidebar = document.querySelector(".sidebar");

if(menu){
    menu.addEventListener("click", () => {
        sidebar.classList.toggle("show");
    });
}