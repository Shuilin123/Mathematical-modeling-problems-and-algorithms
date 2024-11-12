function [] = plot_simulation(U,T)
    %% plot_simulation 温度传播仿真
    % 创建一个新的图形窗口
    % 图像尺寸
    [d,tn]=size(U);
    if length(T)~=tn
        error('环境温度向量和温度矩阵不匹配');
        return;
    end
    w=50;
    map=zeros(w,d*10+1);
    % 初始化图像矩阵
    % 绘制循环
    f=figure('Name','温度变化');
    set(f,'position',[300,100,800,500]);
    ax0=subplot(2,2,[1,2]);%两个位置绘制一个子图
    tu=U(:,1)';
    for i=1:w
       xi=0:0.1:d;
       y=interp1(0:d-1,tu,xi,'cubic');
       map(i,:)=y;
    end
    h0=imagesc(map(:,1:1521));
    colormap jet
    axis equal;
    axis off
    title('温度沿着衣服径向传播情况')
    ax1=subplot(2,2,3);
    h1=animatedline('Marker','*','Color','b');
    title('环境温度变化')
    xlabel('时间/s');
    ylabel('温度/摄氏度');
    ax2=subplot(2,2,4);
    h2=animatedline('Marker','*','Color','r');
    addpoints(h2,1,tu(d));
    title('皮肤外层温度变化');
    xlabel('时间/s');
    ylabel('温度/摄氏度');
    filename='./griaph.gif';
    frame=[];
    fps=10;
    ht1=text(ax1,1.5,37.25,sprintf('%0.2f摄氏度',tu(d)),'Fontsize',10);
    ht2=text(ax2,1.5,37.25,sprintf('%0.2f摄氏度',tu(d)),'Fontsize',10);
    for t = 2:30:tn
        % 生成水平方向的颜色渐变
        % 显示图像
        tu=U(:,t)';
        for i=1:w
           xi=0:0.1:d;
           y=interp1(0:d-1,tu,xi,'cubic');
           map(i,:)=y;
        end
        %imagesc(map(:,1:1521));
        set(h0,'CData',map(:,1:1521));
        addpoints(h1,t,T(t));
        addpoints(h2,t,tu(d));
        %计算相对位置
        xlim = get(ax1, 'XLim');
        ylim = get(ax1, 'YLim');
        set(ht1,'Position',[xlim(1)+(xlim(2)-xlim(1))/1.45,ylim(1)+(ylim(2)-ylim(1))/10,0],'String',sprintf('%.2f摄氏度',tu(d)));
        xlim = get(ax2, 'XLim');
        ylim = get(ax2, 'YLim');
        set(ht2,'Position',[xlim(1)+(xlim(2)-xlim(1))/1.45,ylim(1)+(ylim(2)-ylim(1))/10,0],'String',sprintf('%.2f摄氏度',tu(d)));
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
