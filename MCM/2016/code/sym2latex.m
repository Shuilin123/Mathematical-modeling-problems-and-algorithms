function LaTeX = sym2latex(poly,id)
%SYM2LATEX  将多项式转化为LaTeX样式输出
LaTeX = latex(poly);

% 设置图幅并不显示所有无关的菜单栏等
fig = figure('Name',['poly',num2str(id)]);
fig.NumberTitle= 'off';
fig.MenuBar = 'None';
fig.Position = [300, 300, 600, 300];
fig.Color = 'w';

% 不显示轴
ax = gca;
ax.XTick = [];
ax.YTick = [];
ax.XAxis.Visible = 'off';
ax.YAxis.Visible = 'off';

% 添加text函数
t1 = text(0, .6, ['$$', 'y =', LaTeX,'$$'], 'interpreter', 'latex'); % 注意此处的表达
t1.FontSize = 12;
t1.Color = 'k';
t1.FontWeight = 'Bold';

end