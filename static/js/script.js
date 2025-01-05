// Gestion des animations
document.addEventListener('DOMContentLoaded', () => {
    // Ajouter les animations aux éléments
    const animatedElements = document.querySelectorAll('.card, .form-group');
    animatedElements.forEach(el => el.classList.add('animate-fade-in'));

    // Gestion du formulaire de sondage dynamique
    

    // Initialiser le constructeur de sondage
    surveyBuilder.init();

    // Charts pour les analytics
    const setupCharts = () => {
        const chartCanvas = document.getElementById('surveyChart');
        if (chartCanvas) {
            new Chart(chartCanvas, {
                type: 'bar',
                data: {
                    labels: chartData.labels,
                    datasets: [{
                        label: 'Réponses',
                        data: chartData.data,
                        backgroundColor: 'rgba(74, 144, 226, 0.5)',
                        borderColor: 'rgba(74, 144, 226, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    };

    // Initialiser les charts si nécessaire
    setupCharts();
});

// Notifications toast
const showToast = (message, type = 'success') => {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
};