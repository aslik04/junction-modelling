// Parse the score values (ensure they are numeric)
const algorithmScore = parseFloat("{{ algorithm_metrics.score }}");
const userScore = parseFloat("{{ user_metrics.score }}");
const scoreSpan = document.getElementById('scoreDiff');
if(scoreSpan) {
  // Calculate the difference
  const diff = algorithmScore - userScore;
  // Update the text and set its color based on the value
  scoreSpan.textContent = diff;
  scoreSpan.style.color = diff >= 0 ? 'green' : 'red';
}