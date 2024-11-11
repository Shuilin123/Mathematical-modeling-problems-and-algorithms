function [] = plot_simulation(U)
%% plot_simulation 温度传播仿真
     %% plot_simulation 温度传播仿真
    % 创建一个新的图形窗口
%     x = [0, 153, 153, 0];
%     y = [0, 0, 20, 20];
    % 图像尺寸
    [d,tn]=size(U);
    w=50;
    map=zeros(w,d*10+1);
    % 初始化图像矩阵
    % 绘制循环
    figure('Name','温度变化');
    filename='./griaph.gif';
    frame=[];
    fps=10;
    for t = 1:30:tn
        % 生成水平方向的颜色渐变
        % 显示图像
        tu=U(:,t)';
        for i=1:w
           xi=0:0.1:d;
           y=interp1(0:d-1,tu,xi,'cubic');
           map(i,:)=y;
        end
        imagesc(map(:,1:1521));
        axis equal;
        axis off
        % 暂停一段时间
        pause(0.1);  
        % 如果需要，可以在这里添加代码来保存每一帧的图像
        frame=[frame,{frame2im(getframe(gcf))}];
    end
    for k = 1:length(frame)
        img=frame{k};
		[A, map] = rgb2ind(img, 256); % 将RGB图像转换为索引图像
		if k == 1
			imwrite(A, map, filename, 'gif', 'Loopcount', inf, 'DelayTime', 1/fps);
		else
			imwrite(A, map, filename, 'gif', 'WriteMode', 'append', 'DelayTime', 1/fps);
		end
    end
end