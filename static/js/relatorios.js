/**
 * JavaScript para o Sistema de Relatórios
 * Funcionalidades interativas e controle de gráficos
 */

class RelatorioManager {
    constructor() {
        this.charts = {};
        this.loadingElements = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeComponents();
    }

    setupEventListeners() {
        // Eventos de filtros dinâmicos
        document.addEventListener('change', (e) => {
            if (e.target.matches('.filtro-dinamico')) {
                this.updateCharts();
            }
        });

        // Eventos de exportação
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-export]')) {
                e.preventDefault();
                this.handleExport(e.target.dataset.export, e.target.dataset.type);
            }
        });

        // Eventos de preview
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-preview]')) {
                e.preventDefault();
                this.showPreview(e.target.dataset.preview);
            }
        });
    }

    initializeComponents() {
        // Inicializar tooltips
        this.initTooltips();
        
        // Inicializar tabelas interativas
        this.initDataTables();
        
        // Configurar loading states
        this.setupLoadingStates();
    }

    initTooltips() {
        // Inicializar tooltips do Bootstrap se disponível
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    }

    initDataTables() {
        // Configurar tabelas ordenáveis e filtráveis
        const tables = document.querySelectorAll('.datatable');
        tables.forEach(table => {
            this.makeTableSortable(table);
        });
    }

    makeTableSortable(table) {
        const headers = table.querySelectorAll('th[data-sortable]');
        headers.forEach((header, index) => {
            header.style.cursor = 'pointer';
            header.innerHTML += ' <i class="fas fa-sort text-muted"></i>';
            
            header.addEventListener('click', () => {
                this.sortTable(table, index, header);
            });
        });
    }

    sortTable(table, columnIndex, header) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const isAscending = !header.classList.contains('sort-asc');
        
        // Remover classes de ordenação de outros cabeçalhos
        table.querySelectorAll('th').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
            const icon = th.querySelector('.fas');
            if (icon) {
                icon.className = 'fas fa-sort text-muted';
            }
        });
        
        // Aplicar ordenação
        rows.sort((a, b) => {
            const aValue = this.getCellValue(a.cells[columnIndex]);
            const bValue = this.getCellValue(b.cells[columnIndex]);
            
            if (isAscending) {
                return aValue > bValue ? 1 : -1;
            } else {
                return aValue < bValue ? 1 : -1;
            }
        });
        
        // Atualizar classes e ícones
        header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
        const icon = header.querySelector('.fas');
        if (icon) {
            icon.className = `fas fa-sort-${isAscending ? 'up' : 'down'} text-primary`;
        }
        
        // Reorganizar linhas
        rows.forEach(row => tbody.appendChild(row));
    }

    getCellValue(cell) {
        const text = cell.textContent.trim();
        
        // Tentar converter para número
        const num = parseFloat(text.replace(/[^\d.-]/g, ''));
        if (!isNaN(num)) {
            return num;
        }
        
        // Retornar como string
        return text.toLowerCase();
    }

    setupLoadingStates() {
        // Configurar estados de carregamento para botões
        const loadingButtons = document.querySelectorAll('[data-loading]');
        loadingButtons.forEach(button => {
            button.addEventListener('click', () => {
                this.showButtonLoading(button);
            });
        });
    }

    showButtonLoading(button) {
        const originalText = button.innerHTML;
        const loadingText = button.dataset.loading || 'Carregando...';
        
        button.innerHTML = `<i class="fas fa-spinner fa-spin me-1"></i>${loadingText}`;
        button.disabled = true;
        
        // Restaurar após 3 segundos (ajustar conforme necessário)
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, 3000);
    }

    async updateCharts() {
        try {
            this.showLoadingState('Atualizando gráficos...');
            
            // Coletar filtros atuais
            const filtros = this.getActiveFilters();
            
            // Fazer requisição para API
            const response = await fetch(`/relatorios/api/graficos/${this.getTurmaId()}?${new URLSearchParams(filtros)}`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Atualizar gráficos
            this.updateChartData('graficoBarras', data.barras);
            this.updateChartData('graficoPizza', data.pizza);
            this.updateChartData('graficoLinhas', data.linhas);
            
            this.hideLoadingState();
            
        } catch (error) {
            console.error('Erro ao atualizar gráficos:', error);
            this.showError('Erro ao atualizar os gráficos. Tente novamente.');
            this.hideLoadingState();
        }
    }

    updateChartData(chartId, newData) {
        const chart = this.charts[chartId];
        if (chart && newData) {
            chart.data.labels = newData.labels || [];
            chart.data.datasets[0].data = newData.dados || newData.data || [];
            if (newData.cores) {
                chart.data.datasets[0].backgroundColor = newData.cores;
            }
            chart.update();
        }
    }

    getActiveFilters() {
        const filters = {};
        
        // Coletar valores dos filtros
        const filterInputs = document.querySelectorAll('.filtro-dinamico');
        filterInputs.forEach(input => {
            if (input.value) {
                filters[input.name] = input.value;
            }
        });
        
        return filters;
    }

    getTurmaId() {
        // Obter ID da turma da URL ou elemento de dados
        const pathParts = window.location.pathname.split('/');
        return pathParts[pathParts.length - 1];
    }

    handleExport(format, type = 'completo') {
        const filtros = this.getActiveFilters();
        const turmaId = this.getTurmaId();
        let url;
        
        switch (format) {
            case 'pdf':
                url = `/relatorios/exportar/pdf/${turmaId}?tipo=${type}`;
                break;
            case 'excel':
                url = `/relatorios/exportar/excel/${turmaId}`;
                break;
            default:
                console.error('Formato de exportação não suportado:', format);
                return;
        }
        
        // Adicionar filtros à URL
        const params = new URLSearchParams(filtros);
        if (params.toString()) {
            url += (url.includes('?') ? '&' : '?') + params.toString();
        }
        
        // Abrir URL para download
        const link = document.createElement('a');
        link.href = url;
        link.target = '_blank';
        link.click();
    }

    showPreview(type) {
        const filtros = this.getActiveFilters();
        const turmaId = this.getTurmaId();
        const params = new URLSearchParams(filtros);
        
        let url = `/relatorios/preview/pdf/${turmaId}?tipo=${type}`;
        if (params.toString()) {
            url += '&' + params.toString();
        }
        
        // Abrir preview em nova janela
        window.open(url, '_blank', 'width=800,height=600');
    }

    showLoadingState(message = 'Carregando...') {
        // Criar ou mostrar overlay de loading
        let overlay = document.getElementById('loadingOverlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loadingOverlay';
            overlay.className = 'loading-overlay';
            overlay.innerHTML = `
                <div class="loading-content">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Carregando...</span>
                    </div>
                    <div class="loading-message mt-2">${message}</div>
                </div>
            `;
            document.body.appendChild(overlay);
        } else {
            overlay.querySelector('.loading-message').textContent = message;
            overlay.style.display = 'flex';
        }
    }

    hideLoadingState() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    showError(message) {
        // Mostrar notificação de erro
        const toast = this.createToast('error', 'Erro', message);
        this.showToast(toast);
    }

    showSuccess(message) {
        // Mostrar notificação de sucesso
        const toast = this.createToast('success', 'Sucesso', message);
        this.showToast(toast);
    }

    createToast(type, title, message) {
        const toastContainer = this.getToastContainer();
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : 'success'} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}:</strong> ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        return toast;
    }

    getToastContainer() {
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '1050';
            document.body.appendChild(container);
        }
        return container;
    }

    showToast(toastElement) {
        if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
            const toast = new bootstrap.Toast(toastElement);
            toast.show();
            
            // Remover elemento após ocultar
            toastElement.addEventListener('hidden.bs.toast', () => {
                toastElement.remove();
            });
        }
    }

    // Métodos utilitários para Chart.js
    registerChart(id, chartInstance) {
        this.charts[id] = chartInstance;
    }

    getChart(id) {
        return this.charts[id];
    }

    destroyChart(id) {
        if (this.charts[id]) {
            this.charts[id].destroy();
            delete this.charts[id];
        }
    }

    // Configurações padrão para gráficos
    getDefaultChartConfig() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#1476f2',
                    borderWidth: 1
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        };
    }

    // Paleta de cores profissional
    getColorPalette() {
        return [
            '#1476f2', '#28a745', '#dc3545', '#ffc107', '#17a2b8',
            '#6f42c1', '#e83e8c', '#fd7e14', '#20c997', '#6c757d'
        ];
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    window.relatorioManager = new RelatorioManager();
});

// Funções globais para compatibility
function exportarPDF(tipo = 'completo') {
    if (window.relatorioManager) {
        window.relatorioManager.handleExport('pdf', tipo);
    }
}

function exportarExcel() {
    if (window.relatorioManager) {
        window.relatorioManager.handleExport('excel');
    }
}

function previewPDF(tipo = 'completo') {
    if (window.relatorioManager) {
        window.relatorioManager.showPreview(tipo);
    }
}