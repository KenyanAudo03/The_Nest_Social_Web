document.addEventListener("DOMContentLoaded", function () {
    const players = Array.from(document.querySelectorAll(".plyr-video")).map(
      (video) => {
        // Initialize Plyr
        const player = new Plyr(video, {
          controls: ["play-large", "duration"],
          clickToPlay: true,
          hideControls: false,
          resetOnEnd: true,
          keyboard: false,
          tooltips: { controls: false },
          invertTime: false,
          muted: true,
          fullscreen: { enabled: false },
        });

        // Add click handler to the container
        const container = video.closest(".plyr-container");
        container.addEventListener("click", () => {
          if (player.paused) {
            player.play().catch((error) => {
              console.log("Play failed:", error);
              player.muted = false;
              player.play();
            });
          } else {
            player.pause();
          }
        });

        // Handle play button click separately
        const playButton = container.querySelector(".plyr__control--overlaid");
        if (playButton) {
          playButton.addEventListener("click", (e) => {
            e.stopPropagation();
            if (player.paused) {
              player.play().catch((error) => {
                console.log("Play failed:", error);
                player.muted = false;
                player.play();
              });
            } else {
              player.pause();
            }
          });
        }

        return player;
      }
    );
  });