
// Updated Dual-Provider Configuration
// Generated: 2025-07-25 22:42:07

const DUAL_PROVIDER_CONFIG = {
    system: {
        status: 'PARTIAL_OPERATIONAL',
        workingProviders: 1,
        totalProviders: 2,
        currentDailyCapacity: 200,
        maxDailyCapacity: 220,  // 200 + 20
        monthlyCapacity: 6600   // 6000 + 600
    },
    
    providers: {
        newsdata: {
            status: 'OPERATIONAL',
            enabled: true,
            statusText: 'WORKING ✅',
            statusClass: 'provider-status',
            dailyLimit: 200,
            monthlyLimit: 6000,
            priority: 1,
            responseTime: '~285ms (gRPC optimized)',
            features: ['Categories', 'Search', 'Multi-language', 'Real-time']
        },
        
        currents: {
            status: 'TEMPORARILY_UNAVAILABLE', 
            enabled: false,
            statusText: 'Service Issue ⏳',
            statusClass: 'provider-status unavailable',
            dailyLimit: 20,          // Updated limit
            monthlyLimit: 600,       // Updated limit
            priority: 2,
            planType: 'Basic Plan',
            issue: 'SSL certificate error (service-side)',
            autoRetry: true,
            conservativeMode: true,
            features: ['Categories', 'Search', 'Global coverage'],
            usage: {
                dailyUsed: 0,
                monthlyUsed: 0,
                dailyRemaining: 20,
                monthlyRemaining: 600
            }
        }
    },
    
    performance: {
        grpcOptimization: true,
        traditionalRest: '~850ms',
        grpcOptimized: '~285ms',
        cached: '~5ms',
        speedupFactor: '3x faster'
    },
    
    features: {
        smartCaching: true,
        offlineMode: true,
        autoFailover: true,
        loadBalancing: 'priority_based_conservative',
        rateManagement: true,
        conservativeUsage: true,
        monthlyTracking: true
    },
    
    usage: {
        strategy: 'NewsData.io primary, Currents fallback only',
        rationale: 'Preserve Currents limited quota for emergencies',
        dailyCapacity: '200 (primary) + 20 (fallback) = 220 total',
        monthlyCapacity: '6,000 (primary) + 600 (fallback) = 6,600 total'
    }
};

// Update interface with correct limits
function updateProviderLimits() {
    // Update Currents API limit displays
    const currentsDaily = document.getElementById('currentsDaily');
    const currentsMonthly = document.getElementById('currentsMonthly');
    
    if (currentsDaily) currentsDaily.textContent = '20/day';
    if (currentsMonthly) currentsMonthly.textContent = '600/month';
    
    // Update system capacity displays
    const totalDaily = document.getElementById('totalDaily');
    const totalMonthly = document.getElementById('totalMonthly');
    
    if (totalDaily) totalDaily.textContent = '220/day (when both active)';
    if (totalMonthly) totalMonthly.textContent = '6,600/month (when both active)';
    
    // Add usage strategy info
    const container = document.getElementById('newsContainer');
    if (container && !container.querySelector('.usage-strategy')) {
        const strategyInfo = document.createElement('div');
        strategyInfo.className = 'usage-strategy';
        strategyInfo.innerHTML = `
            <div style="background: #e3f2fd; border: 1px solid #2196f3; border-radius: 8px; padding: 15px; margin: 20px;">
                <h4 style="color: #1976d2; margin-bottom: 10px;">📊 Smart Usage Strategy</h4>
                <p style="color: #1976d2; margin-bottom: 5px;">
                    🥇 <strong>Primary</strong>: NewsData.io (200 requests/day, 6,000/month)<br>
                    🥈 <strong>Fallback</strong>: Currents API (20 requests/day, 600/month)<br>
                    🧠 <strong>Strategy</strong>: Preserve Currents quota for peak times/emergencies<br>
                    📈 <strong>Total Capacity</strong>: 220 requests/day when both active
                </p>
            </div>
        `;
        container.insertBefore(strategyInfo, container.firstChild);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', updateProviderLimits);
