import numpy as np
from scipy.special import expit, logit
from scipy.stats import norm, t as t_dist
from collections import deque

def simulate_binary_contract(S0, K, mu, sigma, T, N_paths=100_000):
    """
    Monte Carlo simulation for a binary contract.
    
    S0:    Current asset price
    K:     Strike / threshold
    mu:    Annual drift
    sigma: Annual volatility
    T:     Time to expiry in years
    N_paths: Number of simulated paths
    """
    # Simulate terminal prices via GBM
    Z = np.random.standard_normal(N_paths)
    S_T = S0 * np.exp((mu - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * Z)
    
    # Binary payoff
    payoffs = (S_T > K).astype(float)
    
    # Estimate and confidence interval
    p_hat = payoffs.mean()
    se = np.sqrt(p_hat * (1 - p_hat) / N_paths)
    ci_lower = p_hat - 1.96 * se
    ci_upper = p_hat + 1.96 * se
    
    return {
        'probability': p_hat,
        'std_error': se,
        'ci_95': (ci_lower, ci_upper),
        'N_paths': N_paths
    }

def brier_score(predictions, outcomes):
    """Evaluate simulation calibration."""
    return np.mean((np.array(predictions) - np.array(outcomes))**2)

def rare_event_IS(S0, K_crash, sigma, T, N_paths=100_000):
    """
    Importance sampling for extreme downside binary contracts.
    
    Example: P(S&P drops 20% in one week)
    """
    K = S0 * (1 - K_crash)  # e.g., 20% crash threshold
    
    # Original drift (risk-neutral)
    mu_original = -0.5 * sigma**2
    
    # Tilted drift: shift the mean toward the crash region
    # Choose mu_tilt so the crash threshold is ~1 std dev away instead of ~4
    log_threshold = np.log(K / S0)
    mu_tilt = log_threshold / T  # center the distribution on the crash
    
    Z = np.random.standard_normal(N_paths)
    
    # Simulate under TILTED measure
    log_returns_tilted = mu_tilt * T + sigma * np.sqrt(T) * Z
    S_T_tilted = S0 * np.exp(log_returns_tilted)
    
    # Likelihood ratio: original density / tilted density
    log_returns_original = mu_original * T + sigma * np.sqrt(T) * Z
    log_LR = (
        -0.5 * ((log_returns_tilted - mu_original * T) / (sigma * np.sqrt(T)))**2
        + 0.5 * ((log_returns_tilted - mu_tilt * T) / (sigma * np.sqrt(T)))**2
    )
    LR = np.exp(log_LR)
    
    # IS estimator
    payoffs = (S_T_tilted < K).astype(float)
    is_estimates = payoffs * LR
    
    p_IS = is_estimates.mean()
    se_IS = is_estimates.std() / np.sqrt(N_paths)
    
    # Compare with crude MC
    Z_crude = np.random.standard_normal(N_paths)
    S_T_crude = S0 * np.exp(mu_original * T + sigma * np.sqrt(T) * Z_crude)
    p_crude = (S_T_crude < K).mean()
    se_crude = np.sqrt(p_crude * (1 - p_crude) / N_paths) if p_crude > 0 else float('inf')
    
    return {
        'p_IS': p_IS, 'se_IS': se_IS,
        'p_crude': p_crude, 'se_crude': se_crude,
        'variance_reduction': (se_crude / se_IS)**2 if se_IS > 0 else float('inf')
    }

class PredictionMarketParticleFilter:
    """
    Sequential Monte Carlo filter for real-time event probability estimation.
    """
    def __init__(self, N_particles=5000, prior_prob=0.5,
                 process_vol=0.05, obs_noise=0.03):
        self.N = N_particles
        self.process_vol = process_vol
        self.obs_noise = obs_noise
        
        # Initialize particles around prior
        logit_prior = logit(prior_prob)
        self.logit_particles = logit_prior + np.random.normal(0, 0.5, N_particles)
        self.weights = np.ones(N_particles) / N_particles
        self.history = []
    
    def update(self, observed_price):
        """Incorporate a new observation (market price, poll result, etc.)"""
        # 1. Propagate: random walk in logit space
        noise = np.random.normal(0, self.process_vol, self.N)
        self.logit_particles += noise
        
        # 2. Convert to probability space
        prob_particles = expit(self.logit_particles)
        
        # 3. Reweight: likelihood of observation given each particle
        log_likelihood = -0.5 * ((observed_price - prob_particles) / self.obs_noise)**2
        log_weights = np.log(self.weights + 1e-300) + log_likelihood
        
        # Normalize in log space for stability
        log_weights -= log_weights.max()
        self.weights = np.exp(log_weights)
        self.weights /= self.weights.sum()
        
        # 4. Check ESS and resample if needed
        ess = 1.0 / np.sum(self.weights**2)
        if ess < self.N / 2:
            self._systematic_resample()
        
        self.history.append(self.estimate())
    
    def _systematic_resample(self):
        """Systematic resampling - lower variance than multinomial."""
        cumsum = np.cumsum(self.weights)
        u = (np.arange(self.N) + np.random.uniform()) / self.N
        indices = np.searchsorted(cumsum, u)
        self.logit_particles = self.logit_particles[indices]
        self.weights = np.ones(self.N) / self.N
    
    def estimate(self):
        """Weighted mean probability estimate."""
        probs = expit(self.logit_particles)
        return np.average(probs, weights=self.weights)
    
    def credible_interval(self, alpha=0.05):
        """Weighted quantile-based credible interval."""
        probs = expit(self.logit_particles)
        sorted_idx = np.argsort(probs)
        sorted_probs = probs[sorted_idx]
        sorted_weights = self.weights[sorted_idx]
        cumw = np.cumsum(sorted_weights)
        lower = sorted_probs[np.searchsorted(cumw, alpha/2)]
        upper = sorted_probs[np.searchsorted(cumw, 1 - alpha/2)]
        return lower, upper

def stratified_binary_mc(S0, K, sigma, T, J=10, N_total=100_000):
    """
    Stratified MC for binary contract pricing.
    Strata defined by quantiles of the terminal price distribution.
    """
    n_per_stratum = N_total // J
    estimates = []
    
    for j in range(J):
        # Uniform draws within stratum [j/J, (j+1)/J]
        U = np.random.uniform(j/J, (j+1)/J, n_per_stratum)
        Z = norm.ppf(U)
        S_T = S0 * np.exp((-0.5*sigma**2)*T + sigma*np.sqrt(T)*Z)
        stratum_mean = (S_T > K).mean()
        estimates.append(stratum_mean)
    
    # Each stratum has weight 1/J
    p_stratified = np.mean(estimates)
    se_stratified = np.std(estimates) / np.sqrt(J)
    
    return p_stratified, se_stratified

def simulate_correlated_outcomes_gaussian(probs, corr_matrix, N=100_000):
    """Gaussian copula no tail dependence."""
    d = len(probs)
    L = np.linalg.cholesky(corr_matrix)
    Z = np.random.standard_normal((N, d))
    X = Z @ L.T
    U = norm.cdf(X)
    outcomes = (U < np.array(probs)).astype(int)
    return outcomes

def simulate_correlated_outcomes_t(probs, corr_matrix, nu=4, N=100_000):
    """Student-t copula symmetric tail dependence."""
    d = len(probs)
    L = np.linalg.cholesky(corr_matrix)
    Z = np.random.standard_normal((N, d))
    X = Z @ L.T
    
    # Divide by sqrt(chi-squared / nu) to get t-distributed
    S = np.random.chisquare(nu, N) / nu
    T = X / np.sqrt(S[:, None])
    U = t_dist.cdf(T, nu)
    outcomes = (U < np.array(probs)).astype(int)
    return outcomes

def simulate_correlated_outcomes_clayton(probs, theta=2.0, N=100_000):
    """Clayton copula (bivariate) lower tail dependence."""
    # Marshall-Olkin algorithm
    V = np.random.gamma(1/theta, 1, N)
    E = np.random.exponential(1, (N, len(probs)))
    U = (1 + E / V[:, None])**(-1/theta)
    outcomes = (U < np.array(probs)).astype(int)
    return outcomes

class PredictionMarketABM:
    """
    Agent-based model of a prediction market order book.
    """
    def __init__(self, true_prob, n_informed=10, n_noise=50, n_mm=5):
        self.true_prob = true_prob
        self.price = 0.50  # initial price
        self.price_history = [self.price]
        
        # Order book (simplified as bid/ask queues)
        self.best_bid = 0.49
        self.best_ask = 0.51
        
        # Agent populations
        self.n_informed = n_informed
        self.n_noise = n_noise
        self.n_mm = n_mm
        
        # Track metrics
        self.volume = 0
        self.informed_pnl = 0
        self.noise_pnl = 0
    
    def step(self):
        """One time step: randomly select an agent to trade."""
        total = self.n_informed + self.n_noise + self.n_mm
        r = np.random.random()
        
        if r < self.n_informed / total:
            self._informed_trade()
        elif r < (self.n_informed + self.n_noise) / total:
            self._noise_trade()
        else:
            self._mm_update()
        
        self.price_history.append(self.price)
    
    def _informed_trade(self):
        """Informed trader: buy if price < true_prob, sell otherwise."""
        signal = self.true_prob + np.random.normal(0, 0.02)  # noisy signal
        
        if signal > self.best_ask + 0.01:  # buy
            size = min(0.1, abs(signal - self.price) * 2)
            self.price += size * self._kyle_lambda()
            self.volume += size
            self.informed_pnl += (self.true_prob - self.best_ask) * size
        elif signal < self.best_bid - 0.01:  # sell
            size = min(0.1, abs(self.price - signal) * 2)
            self.price -= size * self._kyle_lambda()
            self.volume += size
            self.informed_pnl += (self.best_bid - self.true_prob) * size
        
        self.price = np.clip(self.price, 0.01, 0.99)
        self._update_book()
    
    def _noise_trade(self):
        """Noise trader: random buy/sell."""
        direction = np.random.choice([-1, 1])
        size = np.random.exponential(0.02)
        self.price += direction * size * self._kyle_lambda()
        self.price = np.clip(self.price, 0.01, 0.99)
        self.volume += size
        self.noise_pnl -= abs(self.price - self.true_prob) * size * 0.5
        self._update_book()
    
    def _mm_update(self):
        """Market maker: tighten spread toward current price."""
        spread = max(0.02, 0.05 * (1 - self.volume / 100))
        self.best_bid = self.price - spread / 2
        self.best_ask = self.price + spread / 2
    
    def _kyle_lambda(self):
        """Price impact parameter."""
        sigma_v = abs(self.true_prob - self.price) + 0.05
        sigma_u = 0.1 * np.sqrt(self.n_noise)
        return sigma_v / (2 * sigma_u)
    
    def _update_book(self):
        spread = self.best_ask - self.best_bid
        self.best_bid = self.price - spread / 2
        self.best_ask = self.price + spread / 2
    
    def run(self, n_steps=1000):
        for _ in range(n_steps):
            self.step()
        return np.array(self.price_history)
