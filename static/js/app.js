const { useState } = React;

function App() {
    const [prompt, setPrompt] = useState("Can you help me come up with a meal plan for the next 7 days with healthy, in-season, kid-friendly, quick, and delicious meals?");
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('summary');
    const [progress, setProgress] = useState(0);

    // Get API URL - automatically detects localhost for local testing
    // For production, set window.API_URL or update this default
    const getApiUrl = () => {
        if (window.API_URL) return window.API_URL;
        // Auto-detect localhost
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            // return "http://localhost:8080/plan";
            return "http://localhost:8080/plan-meals";
        }
        // Production URL - update this after deployment
        // return "https://mymealplanner-58703261302.us-central1.run.app/plan";
        return "https://mymealplanner-58703261302.us-central1.run.app/plan-meals";
    };
    const API_URL = getApiUrl();

    const handlePlan = async () => {
        setLoading(true);
        setError(null);
        setProgress(0);

        // Simulate progress
        const progressInterval = setInterval(() => {
            setProgress(prev => {
                if (prev >= 90) return prev;
                return prev + 10;
            });
        }, 1000);

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt }),
            });

            clearInterval(progressInterval);
            setProgress(100);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to generate meal plan');
            }

            const data = await response.json();
            setResults(data.structured_data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
            setTimeout(() => setProgress(0), 500);
        }
    };

    if (results) {
        /*
        return <ResultsView 
            results={results} 
            onBack={() => setResults(null)} 
            activeTab={activeTab}
            setActiveTab={setActiveTab}
        />;
        */
        return <ResultsPlanDisplay 
            results={results} 
            onBack={() => setResults(null)} 
            activeTab={activeTab}
            setActiveTab={setActiveTab}
        />; 
    }

    return (
        <div className="container">
            <div className="splash-screen">
                <img 
                    src="static/resources/MyMealPlanner.png" 
                    alt="My Meal Planner" 
                    className="splash-image"
                />
            </div>
            <div className="prompt-section">
                <label className="prompt-label" htmlFor="prompt">
                    What kind of meal plan would you like?
                </label>
                <textarea
                    id="prompt"
                    className="prompt-textarea"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="Enter your meal planning request..."
                />
                <button 
                    className="plan-button" 
                    onClick={handlePlan}
                    disabled={loading || !prompt.trim()}
                >
                    {loading ? 'Planning...' : 'Plan it!'}
                </button>
            </div>

            {loading && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <h2>Creating Your Meal Plan...</h2>
                        <div className="progress-bar-container">
                            <div 
                                className="progress-bar" 
                                style={{ width: `${progress}%` }}
                            />
                        </div>
                        <p className="progress-text">
                            This may take a minute or two...
                        </p>
                    </div>
                </div>
            )}

            {error && (
                <div className="error-message">
                    <strong>Error:</strong> {error}
                </div>
            )}
        </div>
    );
}

function ResultsPlanDisplay({ results, onBack, activeTab, setActiveTab }) {
    // Add state to track checked ingredients
    const [checkedIngredients, setCheckedIngredients] = useState({});

    // Toggle checkbox handler
    const toggleIngredient = (dayIdx, mealType, ingredientIdx) => {
        const key = `${dayIdx}-${mealType}-${ingredientIdx}`;
        setCheckedIngredients(prev => ({
            ...prev,
            [key]: !prev[key]
        }));
    };

    const renderSummary = () => {
        if (!results.days || results.days.length === 0) {
            return <div>No meal plan data available.</div>;
        }

        return results.days.map((day, idx) => (
            <div key={idx} className="day-section">
                <h3 className="day-title">Day {day.dayNumber}</h3>
                {day.date && (
                    <p className="day-subtitle">{day.date}</p>
                )}
                {day.meals && Object.entries(day.meals)
                    .sort(([a], [b]) => {
                        const mealOrder = { breakfast: 0, lunch: 1, dinner: 2 };
                        return (mealOrder[a] ?? 3) - (mealOrder[b] ?? 3);
                    })
                    .map(([mealType, meal]) => (
                    <div key={mealType} className="meal-item">
                        <div className="meal-type">{mealType}</div>
                        <div className="meal-title">
                            {meal.url ? (
                                <a 
                                    href={meal.url} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="meal-link"
                                >
                                    {meal.title}
                                </a>
                            ) : (
                                <span className="meal-text">{meal.title}</span>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        ));
    };

const renderIngredients = () => {
    if (!results.days || results.days.length === 0) {
        return <div>No meal plan data available.</div>;
    }

    return results.days.map((day, idx) => (
        <div key={idx} className="day-section">
            <h3 className="day-title">Day {day.dayNumber} Ingredients</h3>
            {day.meals && Object.entries(day.meals)
                .sort(([a], [b]) => {
                    const mealOrder = { breakfast: 0, lunch: 1, dinner: 2 };
                    return (mealOrder[a.toLowerCase()] ?? 3) - (mealOrder[b.toLowerCase()] ?? 3);
                })
                .map(([mealType, meal]) => {
                // Check if meal has ingredients
                if (!meal.ingredients || Object.keys(meal.ingredients).length === 0) {
                    return null;
                }
                
                return (
                    <div key={mealType}>
                        <h4 className="meal-type">{mealType}</h4>
                        <ul className="ingredient-list">
                            {Object.entries(meal.ingredients).map(([ingredient, quantity], ingIdx) => {
                                const checkboxKey = `${idx}-${mealType}-${ingIdx}`;
                                const isChecked = checkedIngredients[checkboxKey] || false;
                                
                                return (
                                    <li 
                                        key={ingIdx} 
                                        className="ingredient-item"
                                        onClick={() => toggleIngredient(idx, mealType, ingIdx)}
                                        style={{ cursor: 'pointer' }}
                                    >
                                        <input 
                                            type="checkbox" 
                                            checked={isChecked}
                                            onChange={() => {}}
                                            style={{ marginRight: '10px', cursor: 'pointer' }}
                                        />
                                        <span style={{ 
                                            textDecoration: isChecked ? 'line-through' : 'none',
                                            color: isChecked ? '#999' : 'inherit'
                                        }}>
                                            {ingredient} ({quantity || 'to taste'})
                                        </span>
                                    </li>
                                );
                            })}
                        </ul>
                    </div>
                );
            })}
        </div>
    ));
};

    const renderRecipes = () => {
        if (!results.days || results.days.length === 0) {
            return <div>No meal plan data available.</div>;
        }

        return results.days.map((day, idx) => (
            <div key={idx} className="day-section">
                <h3 className="day-title">Day {day.dayNumber} Methods</h3>
                {day.meals && Object.entries(day.meals)
                .sort(([a], [b]) => {
                    const mealOrder = { breakfast: 0, lunch: 1, dinner: 2 };
                    return (mealOrder[a.toLowerCase()] ?? 3) - (mealOrder[b.toLowerCase()] ?? 3);
                })
                .map(([mealType, meal]) => {
                    // Check if meal has methods
                    if (!meal.method) {
                        return null;
                    }
                    
                    return (
                        <div key={mealType}>
                            <h4 className="meal-type">{mealType}</h4>
                                {meal.url && (
                                    <a 
                                        href={meal.url} 
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                        className="recipe-link"
                                    >
                                        {meal.title}
                                    </a>
                                )}
                                {meal.method && (
                                    <div className="recipe-item">
                                        <h5>Method:</h5>
                                        <ol className="method-list">
                                            {meal.method
                                                .split('.')
                                                .map(sentence => sentence.trim())
                                                .filter(sentence => sentence.length > 0)
                                                .map((sentence, stepIdx) => (
                                                    <li key={stepIdx} className="method-step">
                                                        {sentence}.
                                                    </li>
                                                ))}
                                        </ol>
                                    </div>
                                )}
                        </div>
                    );
                })}
            </div>
        ));
    }

  return (
            <div className="container">
            <div className="results-container">
                <div className="results-header">
                    <h2 className="results-title">Your Meal Plan</h2>
                    <button className="back-button" onClick={onBack}>
                        ← New Plan
                    </button>
                </div>

                <div className="tabs">
                    <button 
                        className={`tab ${activeTab === 'summary' ? 'active' : ''}`}
                        onClick={() => setActiveTab('summary')}
                    >
                        Summary
                    </button>
                    <button 
                        className={`tab ${activeTab === 'ingredients' ? 'active' : ''}`}
                        onClick={() => setActiveTab('ingredients')}
                    >
                        Ingredients
                    </button>
                    <button 
                        className={`tab ${activeTab === 'recipes' ? 'active' : ''}`}
                        onClick={() => setActiveTab('recipes')}
                    >
                        Recipes
                    </button>
                </div>

                <div className={`tab-content ${activeTab === 'summary' ? 'active' : ''}`}>
                    {renderSummary()}
                </div>

                <div className={`tab-content ${activeTab === 'ingredients' ? 'active' : ''}`}>
                    {renderIngredients()}
                </div>

                <div className={`tab-content ${activeTab === 'recipes' ? 'active' : ''}`}>
                    {renderRecipes()}
                </div>
            </div>
        </div>
    );
}

ReactDOM.render(<App />, document.getElementById('root'));