// Add this in your base template or somewhere accessible

const csrftoken = document.querySelector("[name=csrfmiddlewaretoken]").value;

document.addEventListener("DOMContentLoaded", () => {
  document.body.addEventListener("click", async (event) => {
    if (event.target.closest(".like-button")) {
      const button = event.target.closest(".like-button");
      const postId = button.getAttribute("data-post-id");
      const likeIcon = button.querySelector("i");
      const likeCount = button.querySelector(".like-count");

      // Add animation class
      likeCount.classList.add("animate");

      try {
        const response = await fetch(`/toggle_like/${postId}/`, {
          method: "POST",
          headers: {
            "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")
              .value,
            "Content-Type": "application/json",
          },
        });

        if (response.ok) {
          const data = await response.json();
          likeCount.textContent = data.like_count;

          // Toggle between filled and outlined heart icons
          if (data.is_liked) {
            likeIcon.classList.remove("bx-heart");
            likeIcon.classList.add("bxs-heart");
          } else {
            likeIcon.classList.remove("bxs-heart");
            likeIcon.classList.add("bx-heart");
          }
        }
      } catch (error) {
        console.error("Error:", error);
      }

      // Remove animation class after animation completes
      setTimeout(() => {
        likeCount.classList.remove("animate");
      }, 300);
    }
  });
});
