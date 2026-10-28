/**
 * Coreva landing page — mobile navigation.
 *
 * Uses a single class toggle. All styling is in the CSS file.
 */

document.addEventListener("DOMContentLoaded", function () {

    const toggle = document.getElementById("cvMobileToggle");

    if (!toggle) {
        return;
    }


    /* -------------------------------------------------
       Toggle the mobile menu
       ------------------------------------------------- */

    toggle.addEventListener("click", function (event) {

        event.stopPropagation();

        const existingMenu = document.querySelector(".cv-mobile-menu");

        if (existingMenu) {
            existingMenu.remove();
            toggle.setAttribute("aria-expanded", "false");
            return;
        }


        const menu = document.createElement("div");

        menu.className = "cv-mobile-menu";

        menu.innerHTML = `
            <a href="#features">Features</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#contractors">Contractors</a>
            <a href="#pricing">Pricing</a>
            <a href="#faq">FAQ</a>
            <a href="/accounts/login/" class="cv-mobile-menu-login">Sign in</a>
            <a href="/accounts/register/" class="cv-mobile-menu-button">Start Free Trial</a>
        `;


        /* Close menu when a link is tapped */

        menu.querySelectorAll("a").forEach(function (link) {

            link.addEventListener("click", function () {
                menu.remove();
                toggle.setAttribute("aria-expanded", "false");
            });

        });


        toggle.setAttribute("aria-expanded", "true");

        document.body.appendChild(menu);

    });


    /* -------------------------------------------------
       Close the menu when clicking outside
       ------------------------------------------------- */

    document.addEventListener("click", function (event) {

        const menu = document.querySelector(".cv-mobile-menu");

        if (!menu) {
            return;
        }


        if (!menu.contains(event.target)) {
            menu.remove();
            toggle.setAttribute("aria-expanded", "false");
        }

    });


    /* -------------------------------------------------
       Close the menu on Escape
       ------------------------------------------------- */

    document.addEventListener("keydown", function (event) {

        if (event.key !== "Escape") {
            return;
        }


        const menu = document.querySelector(".cv-mobile-menu");

        if (menu) {
            menu.remove();
            toggle.setAttribute("aria-expanded", "false");
        }

    });

});