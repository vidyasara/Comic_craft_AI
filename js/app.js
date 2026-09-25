document.addEventListener(
    "DOMContentLoaded",
    () => {

        const form =
            document.getElementById(
                "comic-form"
            );

        const button =
            document.getElementById(
                "generate-button"
            );


        if (form && button) {

            form.addEventListener(
                "submit",
                () => {

                    button.disabled = true;

                    button.textContent =
                        "Creating your comic…";

                }
            );

        }


        document
            .querySelectorAll(".download-pdf")
            .forEach((link) => {

                link.addEventListener(
                    "click",
                    async (event) => {

                        event.preventDefault();

                        const original =
                            link.textContent;

                        link.textContent =
                            "Preparing PDF…";

                        link.style.pointerEvents =
                            "none";


                        try {

                            const response =
                                await fetch(
                                    link.href
                                );


                            if (!response.ok) {

                                throw new Error(
                                    "PDF download failed."
                                );

                            }


                            const blob =
                                await response.blob();


                            const objectUrl =
                                URL.createObjectURL(
                                    blob
                                );


                            const anchor =
                                document.createElement(
                                    "a"
                                );


                            anchor.href =
                                objectUrl;


                            anchor.download =
                                "comiccraft-comic.pdf";


                            document.body.appendChild(
                                anchor
                            );


                            anchor.click();


                            anchor.remove();


                            URL.revokeObjectURL(
                                objectUrl
                            );


                            const successUrl =
                                link.dataset.successUrl;


                            if (successUrl) {

                                window.location.href =
                                    successUrl;

                            }

                        } catch (error) {

                            window.location.href =
                                link.href;

                        } finally {

                            link.textContent =
                                original;

                            link.style.pointerEvents =
                                "";

                        }

                    }
                );

            });

    }
);