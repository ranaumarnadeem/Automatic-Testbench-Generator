module counter(input clk, input rst, input en, output reg [3:0] count);
  always @(posedge clk or posedge rst) begin
    if (rst)
      count <= 0;
    else if (en)
      count <= count + 1;
  end
endmodule



// ---- Auto-generated testbench ----
`timescale 1ns/1ps
module counter_tb;
// Declare inputs and outputs
    reg clk;
    reg rst;
    reg en;
    wire [3:0] count;

// Instantiate DUT
    counter uut (
        .clk(clk),
        .rst(rst),
        .en(en),
        .count(count)
    );

// Clock generation
    initial clk = 0;
    always #5 clk = ~clk;

initial begin
    rst = 1; #10; rst = 0;
        #10 en = 0;
        #10 en = 1;
        $finish;
end
endmodule